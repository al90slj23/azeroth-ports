package io.github.al90slj23.azerothsurvivors;

import java.io.ByteArrayOutputStream;
import java.io.Closeable;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.net.SocketException;
import java.net.SocketTimeoutException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** Serves only indexed game assets to a browser on this device. No filesystem or proxy routes. */
public final class LocalHttpServer implements Closeable {
    public interface Source {
        InputStream open(String path) throws IOException;
        long length(String path) throws IOException;
        default String revision() { return "1"; }
    }

    private static final int LINE_LIMIT = 4096;
    private static final int HEADER_LIMIT = 16384;
    private static final int REQUEST_TIMEOUT_MS = 10000;
    private final int requestedPort;
    private final Source source;
    private final Set<Socket> clients = ConcurrentHashMap.newKeySet();
    private volatile ServerSocket listener;
    private volatile boolean closed;
    private ThreadPoolExecutor workers;

    public LocalHttpServer(int port, Source source) {
        if (port < 0 || port > 65535 || source == null) throw new IllegalArgumentException();
        this.requestedPort = port;
        this.source = source;
    }

    public synchronized void start() throws IOException {
        if (closed || listener != null) throw new IllegalStateException("Server has already started or closed");
        ServerSocket socket = new ServerSocket();
        try {
            socket.setReuseAddress(true);
            socket.bind(new InetSocketAddress(InetAddress.getByName("127.0.0.1"), requestedPort), 32);
        } catch (IOException error) {
            closeQuietly(socket);
            throw error;
        }
        workers = new ThreadPoolExecutor(6, 6, 30, TimeUnit.SECONDS,
                new ArrayBlockingQueue<Runnable>(64), daemonFactory("game-http-worker"));
        workers.allowCoreThreadTimeOut(true);
        listener = socket;
        Thread accept = daemonFactory("game-http-accept").newThread(this::acceptLoop);
        accept.start();
    }

    public int getPort() {
        ServerSocket socket = listener;
        return socket == null ? requestedPort : socket.getLocalPort();
    }

    private void acceptLoop() {
        while (!closed) {
            Socket client = null;
            try {
                client = listener.accept();
                client.setSoTimeout(REQUEST_TIMEOUT_MS);
                client.setTcpNoDelay(true);
                clients.add(client);
                if (closed) { closeClient(client); break; }
                final Socket accepted = client;
                workers.execute(() -> handle(accepted));
            } catch (RejectedExecutionException error) {
                if (client != null) {
                    try { reply(client.getOutputStream(), 503, null, 0); } catch (IOException ignored) { }
                    closeClient(client);
                }
            } catch (IOException error) {
                if (client != null) closeClient(client);
                if (closed || error instanceof SocketException) break;
            }
        }
    }

    private void handle(Socket client) {
        boolean headersSent = false;
        try {
            InputStream input = client.getInputStream();
            OutputStream output = client.getOutputStream();
            String line = readLine(input, LINE_LIMIT);
            if (line == null) return;
            String[] request = line.split(" ", -1);
            if (request.length != 3 || !("HTTP/1.1".equals(request[2]) || "HTTP/1.0".equals(request[2]))) {
                throw new HttpFailure(400);
            }
            Map<String, String> headers = new HashMap<>();
            int headerBytes = line.length() + 2;
            while (true) {
                line = readLine(input, LINE_LIMIT);
                if (line == null) throw new HttpFailure(400);
                headerBytes += line.length() + 2;
                if (headerBytes > HEADER_LIMIT) throw new HttpFailure(431);
                if (line.isEmpty()) break;
                int colon = line.indexOf(':');
                if (colon < 1) throw new HttpFailure(400);
                String key = line.substring(0, colon).toLowerCase(Locale.ROOT);
                if (!key.matches("[a-z0-9!#$%&'*+.^_`|~-]+") || headers.containsKey(key)) throw new HttpFailure(400);
                headers.put(key, line.substring(colon + 1).trim());
            }
            String host = headers.get("host");
            if (host == null && "HTTP/1.1".equals(request[2])) throw new HttpFailure(400);
            if (host != null && !(host.equals("127.0.0.1:" + getPort()) || host.equals("localhost:" + getPort()))) {
                throw new HttpFailure(403);
            }
            String origin = headers.get("origin");
            if (origin != null && !(origin.equals("http://127.0.0.1:" + getPort())
                    || origin.equals("http://localhost:" + getPort()))) throw new HttpFailure(403);
            if (!("GET".equals(request[0]) || "HEAD".equals(request[0]))) {
                Map<String, String> extra = new HashMap<>();
                extra.put("Allow", "GET, HEAD");
                reply(output, 405, extra, 0);
                return;
            }
            String path = assetPath(request[1]);
            long length = source.length(path);
            if (length < 0) throw new FileNotFoundException(path);
            String etag = assetTag(source.revision(), path, length);
            Map<String, String> extra = new HashMap<>();
            // A new APK can replace files under the same loopback origin. Revalidate even
            // game data, while ETags let the original boot prefetch reuse cached bytes.
            extra.put("Cache-Control", "no-cache");
            extra.put("ETag", etag);
            extra.put("X-Content-Type-Options", "nosniff");
            extra.put("Content-Security-Policy", "frame-src 'none'; object-src 'none'; base-uri 'self'");
            if (matchesTag(headers.get("if-none-match"), etag)) {
                reply(output, 304, extra, -1);
                return;
            }
            ByteRange range = null;
            if ("GET".equals(request[0])) range = ByteRange.parse(headers.get("range"), length);
            long start = range == null ? 0 : range.start;
            long count = range == null ? length : range.end - range.start + 1;
            extra.put("Content-Type", mime(path));
            extra.put("Accept-Ranges", "bytes");
            if (range != null) extra.put("Content-Range", "bytes " + range.start + "-" + range.end + "/" + length);
            if ("HEAD".equals(request[0])) {
                reply(output, 200, extra, length);
                return;
            }
            try (InputStream body = source.open(path)) {
                if (body == null) throw new FileNotFoundException(path);
                skipFully(body, start);
                reply(output, range == null ? 200 : 206, extra, count);
                headersSent = true;
                byte[] buffer = new byte[32768];
                long remaining = count;
                while (remaining > 0 && !closed) {
                    int read = body.read(buffer, 0, (int) Math.min(buffer.length, remaining));
                    if (read < 0) throw new IOException("Asset ended before its indexed length");
                    if (read == 0) continue;
                    output.write(buffer, 0, read);
                    remaining -= read;
                }
                output.flush();
            }
        } catch (HttpFailure failure) {
            if (!headersSent) {
                try {
                    Map<String, String> extra = null;
                    if (failure.contentRange != null) {
                        extra = new HashMap<>();
                        extra.put("Content-Range", failure.contentRange);
                    }
                    reply(client.getOutputStream(), failure.status, extra, 0);
                } catch (IOException ignored) { }
            }
        } catch (SocketTimeoutException timeout) {
            if (!headersSent) try { reply(client.getOutputStream(), 408, null, 0); } catch (IOException ignored) { }
        } catch (IOException error) {
            if (!headersSent) try {
                reply(client.getOutputStream(), error instanceof FileNotFoundException ? 404 : 500, null, 0);
            } catch (IOException ignored) { }
        } catch (RuntimeException error) {
            if (!headersSent) try { reply(client.getOutputStream(), 500, null, 0); } catch (IOException ignored) { }
        } finally {
            // Discard only bytes already waiting after a rejected header. This avoids a
            // reset hiding a short error response, without waiting for an untrusted body.
            try {
                InputStream pending = client.getInputStream();
                byte[] discard = new byte[1024];
                int drained = 0;
                while (drained < HEADER_LIMIT && pending.available() > 0) {
                    int count = pending.read(discard, 0, Math.min(discard.length,
                            Math.min(pending.available(), HEADER_LIMIT - drained)));
                    if (count < 0) break;
                    drained += count;
                }
            } catch (IOException ignored) { }
            closeClient(client);
        }
    }

    private static String readLine(InputStream input, int limit) throws IOException, HttpFailure {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        while (true) {
            int value = input.read();
            if (value < 0) {
                if (bytes.size() == 0) return null;
                throw new HttpFailure(400);
            }
            if (value == '\r') {
                if (input.read() != '\n') throw new HttpFailure(400);
                return new String(bytes.toByteArray(), StandardCharsets.ISO_8859_1);
            }
            if (value == '\n' || value == 0 || (value < 32 && value != '\t') || value == 127) throw new HttpFailure(400);
            if (bytes.size() >= limit) throw new HttpFailure(431);
            bytes.write(value);
        }
    }

    private static String assetPath(String target) throws HttpFailure {
        if (!target.startsWith("/") || target.startsWith("//") || target.indexOf('#') >= 0) throw new HttpFailure(400);
        for (int i = 0; i < target.length(); i++) {
            char c = target.charAt(i);
            if (c <= 32 || c >= 127 || c == '\\') throw new HttpFailure(400);
        }
        String raw = target.split("\\?", 2)[0];
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        for (int i = 0; i < raw.length(); i++) {
            int c = raw.charAt(i);
            if (c == '%') {
                if (i + 2 >= raw.length()) throw new HttpFailure(400);
                int high = Character.digit(raw.charAt(++i), 16);
                int low = Character.digit(raw.charAt(++i), 16);
                if (high < 0 || low < 0) throw new HttpFailure(400);
                c = high * 16 + low;
                if (c == '/' || c == '\\') throw new HttpFailure(400);
            }
            bytes.write(c);
        }
        final String decoded;
        try {
            decoded = StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes.toByteArray())).toString();
        } catch (CharacterCodingException invalid) { throw new HttpFailure(400); }
        for (int i = 0; i < decoded.length(); i++) {
            char c = decoded.charAt(i);
            if (c < 32 || c == 127 || c == '\\' || c == ':') throw new HttpFailure(400);
        }
        String path = decoded.substring(1);
        for (String segment : path.split("/", -1)) {
            if (segment.equals(".") || segment.equals("..")) throw new HttpFailure(400);
        }
        return path.isEmpty() ? "index.html" : path;
    }

    private static void skipFully(InputStream input, long bytes) throws IOException {
        while (bytes > 0) {
            long skipped = input.skip(bytes);
            if (skipped > 0) { bytes -= skipped; continue; }
            if (input.read() < 0) throw new IOException("Range starts after asset end");
            bytes--;
        }
    }

    private static String mime(String path) {
        String name = path.toLowerCase(Locale.ROOT);
        if (name.endsWith(".html")) return "text/html; charset=utf-8";
        if (name.endsWith(".js") || name.endsWith(".mjs")) return "text/javascript; charset=utf-8";
        if (name.endsWith(".css")) return "text/css; charset=utf-8";
        if (name.endsWith(".wasm")) return "application/wasm";
        if (name.endsWith(".json")) return "application/json";
        if (name.endsWith(".ttf")) return "font/ttf";
        if (name.endsWith(".otf")) return "font/otf";
        if (name.endsWith(".woff2")) return "font/woff2";
        if (name.endsWith(".woff")) return "font/woff";
        if (name.endsWith(".png")) return "image/png";
        if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "image/jpeg";
        if (name.endsWith(".svg")) return "image/svg+xml";
        if (name.endsWith(".ico")) return "image/x-icon";
        if (name.endsWith(".ogg")) return "audio/ogg";
        if (name.endsWith(".mp3")) return "audio/mpeg";
        if (name.endsWith(".wav")) return "audio/wav";
        return "application/octet-stream";
    }

    private static String assetTag(String revision, String path, long length) {
        try {
            byte[] hash = MessageDigest.getInstance("SHA-256").digest(
                    (String.valueOf(revision) + "\0" + path + "\0" + length).getBytes(StandardCharsets.UTF_8));
            StringBuilder result = new StringBuilder("\"");
            char[] hex = "0123456789abcdef".toCharArray();
            for (byte b : hash) result.append(hex[(b & 255) >>> 4]).append(hex[b & 15]);
            return result.append('"').toString();
        } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }

    private static boolean matchesTag(String condition, String tag) {
        if (condition == null) return false;
        for (String candidate : condition.split(",")) {
            candidate = candidate.trim();
            if (candidate.equals("*") || candidate.equals(tag) || candidate.equals("W/" + tag)) return true;
        }
        return false;
    }

    private static void reply(OutputStream output, int status, Map<String, String> headers, long length) throws IOException {
        String reason;
        switch (status) {
            case 200: reason = "OK"; break;
            case 206: reason = "Partial Content"; break;
            case 304: reason = "Not Modified"; break;
            case 400: reason = "Bad Request"; break;
            case 403: reason = "Forbidden"; break;
            case 404: reason = "Not Found"; break;
            case 405: reason = "Method Not Allowed"; break;
            case 408: reason = "Request Timeout"; break;
            case 416: reason = "Range Not Satisfiable"; break;
            case 431: reason = "Request Header Fields Too Large"; break;
            case 503: reason = "Service Unavailable"; break;
            default: reason = "Internal Server Error";
        }
        StringBuilder data = new StringBuilder("HTTP/1.1 ").append(status).append(' ').append(reason)
                .append("\r\nConnection: close\r\n");
        if (length >= 0) data.append("Content-Length: ").append(length).append("\r\n");
        if (status >= 400) data.append("Cache-Control: no-store\r\n");
        if (headers != null) for (Map.Entry<String, String> header : headers.entrySet()) {
            data.append(header.getKey()).append(": ").append(header.getValue()).append("\r\n");
        }
        data.append("\r\n");
        output.write(data.toString().getBytes(StandardCharsets.ISO_8859_1));
        output.flush();
    }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        closeQuietly(listener);
        for (Socket socket : clients) closeClient(socket);
        if (workers != null) workers.shutdownNow();
    }

    private void closeClient(Socket client) {
        clients.remove(client);
        closeQuietly(client);
    }

    private static void closeQuietly(Closeable object) {
        if (object != null) try { object.close(); } catch (IOException ignored) { }
    }

    private static ThreadFactory daemonFactory(String name) {
        AtomicInteger counter = new AtomicInteger();
        return runnable -> {
            Thread thread = new Thread(runnable, name + "-" + counter.incrementAndGet());
            thread.setDaemon(true);
            return thread;
        };
    }

    private static final class HttpFailure extends Exception {
        final int status;
        final String contentRange;
        HttpFailure(int status) { this(status, null); }
        HttpFailure(int status, String contentRange) { this.status = status; this.contentRange = contentRange; }
    }

    private static final class ByteRange {
        final long start;
        final long end;
        ByteRange(long start, long end) { this.start = start; this.end = end; }
        static ByteRange parse(String value, long length) throws HttpFailure {
            if (value == null || !value.startsWith("bytes=")) return null;
            String text = value.substring(6);
            int dash = text.indexOf('-');
            try {
                if (dash < 0 || text.indexOf(',', 0) >= 0 || text.indexOf('-', dash + 1) >= 0 || length == 0) throw new NumberFormatException();
                String first = text.substring(0, dash);
                String last = text.substring(dash + 1);
                if ((!first.isEmpty() && !first.matches("[0-9]+")) || (!last.isEmpty() && !last.matches("[0-9]+"))) throw new NumberFormatException();
                if (first.isEmpty()) {
                    long suffix = Long.parseLong(last);
                    if (suffix <= 0) throw new NumberFormatException();
                    return new ByteRange(Math.max(0, length - suffix), length - 1);
                }
                long start = Long.parseLong(first);
                long end = last.isEmpty() ? length - 1 : Math.min(Long.parseLong(last), length - 1);
                if (start >= length || end < start) throw new NumberFormatException();
                return new ByteRange(start, end);
            } catch (NumberFormatException invalid) { throw new HttpFailure(416, "bytes */" + length); }
        }
    }
}
