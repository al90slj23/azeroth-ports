import io.github.al90slj23.azerothsurvivors.LocalHttpServer;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.net.Socket;
import java.net.SocketException;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/** Host-JVM integration tests; no Android emulator or third-party test framework needed. */
public final class LocalHttpServerTest {
    private static int assertions;
    private static final byte[] WASM = {0, 97, 115, 109, 1, 0, 0, 0};

    public static void main(String[] args) throws Exception {
        final Map<String, byte[]> files = new HashMap<>();
        files.put("index.html", "<h1>Game</h1>".getBytes(StandardCharsets.UTF_8));
        files.put("client.wasm", WASM);
        files.put("data/map", "0123456789".getBytes(StandardCharsets.UTF_8));
        files.put("data/__index", "[]".getBytes(StandardCharsets.UTF_8));
        files.put("data/fonts/azs_sc.ttf", new byte[] {1, 2});
        files.put("literal+name.txt", new byte[] {3});
        files.put("中文.txt", new byte[] {4});
        files.put("empty", new byte[0]);
        final AtomicInteger streams = new AtomicInteger();
        final AtomicInteger lookups = new AtomicInteger();
        final AtomicReference<String> revision = new AtomicReference<>("test-a");
        LocalHttpServer.Source source = new LocalHttpServer.Source() {
            public String revision() { return revision.get(); }
            public long length(String path) throws IOException {
                lookups.incrementAndGet();
                if (path.equals("broken")) throw new IOException("Source failure");
                byte[] bytes = files.get(path);
                if (bytes == null) throw new FileNotFoundException(path);
                return bytes.length;
            }
            public InputStream open(String path) throws IOException {
                byte[] bytes = files.get(path);
                if (bytes == null) throw new FileNotFoundException(path);
                streams.incrementAndGet();
                return new ByteArrayInputStream(bytes) {
                    @Override public void close() throws IOException { super.close(); streams.decrementAndGet(); }
                };
            }
        };
        LocalHttpServer server = new LocalHttpServer(0, source);
        try {
            server.start();
            check(server.getPort() > 0, "ephemeral loopback port");
            Response index = request(server, "GET", "/?v=425f2391", null);
            equal(200, index.status, "root page");
            equal("<h1>Game</h1>", index.text(), "index body");
            equal("text/html; charset=utf-8", index.headers.get("content-type"), "HTML MIME");
            equal("no-cache", index.headers.get("cache-control"), "entry cache");
            Response wasm = request(server, "GET", "/client.wasm?v=1", null);
            check(Arrays.equals(WASM, wasm.body), "binary WASM intact");
            equal("application/wasm", wasm.headers.get("content-type"), "WASM MIME");
            equal("nosniff", wasm.headers.get("x-content-type-options"), "nosniff");
            equal("font/ttf", request(server, "GET", "/data/fonts/azs_sc.ttf", null).headers.get("content-type"), "CJK MIME");
            Response head = request(server, "HEAD", "/client.wasm", null);
            equal(200, head.status, "HEAD status");
            equal("8", head.headers.get("content-length"), "HEAD represents asset length");
            equal(0, head.body.length, "HEAD has no body");
            equal(0, streams.get(), "HEAD does not retain/open streams");
            equal("no-cache", request(server, "GET", "/data/map", null).headers.get("cache-control"), "data revalidates across APK upgrades");
            equal("no-cache", request(server, "GET", "/data/__index", null).headers.get("cache-control"), "index refreshes");
            String tag = wasm.headers.get("etag");
            check(tag != null && tag.startsWith("\"") && tag.endsWith("\""), "asset ETag");
            Response unchanged = request(server, "GET", "/client.wasm", "If-None-Match: " + tag + "\r\n");
            equal(304, unchanged.status, "conditional cache validation");
            equal(0, unchanged.body.length, "304 has no body");
            equal(tag, unchanged.headers.get("etag"), "304 retains validator");
            equal(304, request(server, "HEAD", "/client.wasm", "If-None-Match: W/" + tag + "\r\n").status, "HEAD weak validation");
            revision.set("test-b");
            Response upgraded = request(server, "GET", "/client.wasm", "If-None-Match: " + tag + "\r\n");
            equal(200, upgraded.status, "new APK revision invalidates same-size asset");
            check(!tag.equals(upgraded.headers.get("etag")), "revision changes validator");
            equal(200, request(server, "GET", "/literal+name.txt", null).status, "plus remains literal in path");
            equal(200, request(server, "GET", "/%E4%B8%AD%E6%96%87.txt", null).status, "valid UTF-8 filename");

            int priorLookups = lookups.get();
            for (String path : new String[] {"/%", "/%XY", "/%00", "/%ff", "/../private", "/%2e%2e/private",
                    "/data/../../private", "/data%2fprivate", "/data%5cprivate", "/data\\private", "//other.test/data", "https://other.test/data", "/path#fragment"}) {
                equal(400, request(server, "GET", path, null).status, "reject " + path);
            }
            equal(priorLookups, lookups.get(), "unsafe paths never reach asset source");
            equal(404, request(server, "GET", "/missing", null).status, "missing asset");
            equal(500, request(server, "GET", "/broken", null).status, "source error bounded");
            Response post = request(server, "POST", "/", null);
            equal(405, post.status, "method rejected");
            equal("GET, HEAD", post.headers.get("allow"), "allowed methods");
            equal(403, request(server, "GET", "/", "Origin: https://unrelated.example\r\n").status, "foreign origin rejected");
            equal(403, raw(server, "GET / HTTP/1.1\r\nHost: external.example\r\n\r\n").status, "foreign host rejected");
            equal(400, raw(server, "GET / HTTP/1.1\r\nHost: localhost:" + server.getPort() + "\r\nHost: localhost\r\n\r\n").status, "duplicate header rejected");
            equal(400, raw(server, "GET / HTTP/1.1\n\n").status, "malformed line endings rejected");
            equal(400, raw(server, "GET / HTTP/1.1\r\n\r\n").status, "HTTP1.1 requires Host");
            equal(431, request(server, "GET", "/", "Long: " + repeat('x', 4100) + "\r\n").status, "oversized line rejected");
            StringBuilder many = new StringBuilder();
            for (int i = 0; i < 7; i++) many.append("Long-").append(i).append(": ").append(repeat('x', 2500)).append("\r\n");
            equal(431, request(server, "GET", "/", many.toString()).status, "bounded total headers");

            Response range = request(server, "GET", "/data/map", "Range: bytes=2-5\r\n");
            equal(206, range.status, "byte range");
            equal("2345", range.text(), "range body");
            equal("4", range.headers.get("content-length"), "range length");
            equal("bytes 2-5/10", range.headers.get("content-range"), "range metadata");
            equal("789", request(server, "GET", "/data/map", "Range: bytes=-3\r\n").text(), "suffix range");
            equal("89", request(server, "GET", "/data/map", "Range: bytes=8-\r\n").text(), "open end range");
            equal("89", request(server, "GET", "/data/map", "Range: bytes=8-500\r\n").text(), "end clamped");
            for (String value : new String[] {"bytes=10-", "bytes=5-2", "bytes=-0", "bytes=0-1,3-4", "bytes=9223372036854775808-"}) {
                Response bad = request(server, "GET", "/data/map", "Range: " + value + "\r\n");
                equal(416, bad.status, "invalid range " + value);
                equal("bytes */10", bad.headers.get("content-range"), "invalid range size");
            }
            equal(416, request(server, "GET", "/empty", "Range: bytes=0-\r\n").status, "empty range invalid");
            equal(200, request(server, "HEAD", "/data/map", "Range: bytes=2-3\r\n").status, "HEAD ignores range");
            equal(0, streams.get(), "all response streams closed");
            equal(200, request(server, "GET", "/", null).status, "still available after invalid requests");

            Socket unfinished = new Socket("127.0.0.1", server.getPort());
            unfinished.setSoTimeout(1500);
            unfinished.getOutputStream().write("GET / HTTP/1.1\r\n".getBytes(StandardCharsets.US_ASCII));
            Thread.sleep(25);
            server.close();
            boolean disconnected;
            try { disconnected = unfinished.getInputStream().read() == -1; }
            catch (SocketException reset) { disconnected = true; }
            check(disconnected, "close cancels partial requests");
            unfinished.close();
            server.close();
            boolean refused = false;
            try { new Socket("127.0.0.1", server.getPort()).close(); } catch (IOException expected) { refused = true; }
            check(refused, "listener closed");
        } finally { server.close(); }
        System.out.println("LocalHttpServer: " + assertions + " assertions passed");
    }

    private static Response request(LocalHttpServer server, String method, String path, String extra) throws IOException {
        return raw(server, method + " " + path + " HTTP/1.1\r\nHost: 127.0.0.1:" + server.getPort()
                + "\r\n" + (extra == null ? "" : extra) + "\r\n");
    }
    private static Response raw(LocalHttpServer server, String request) throws IOException {
        try (Socket socket = new Socket("127.0.0.1", server.getPort())) {
            socket.setSoTimeout(2000);
            socket.getOutputStream().write(request.getBytes(StandardCharsets.ISO_8859_1));
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[4096];
            int n;
            while ((n = socket.getInputStream().read(buffer)) >= 0) {
                bytes.write(buffer, 0, n);
                // The server closes each connection; a completed Content-Length message
                // is still complete if a rejected/pipelined input later causes a reset.
                String partial = bytes.toString("ISO-8859-1");
                int end = partial.indexOf("\r\n\r\n");
                if (end >= 0) {
                    if (request.startsWith("HEAD ") || partial.startsWith("HTTP/1.1 304 ")) break;
                    java.util.regex.Matcher length = java.util.regex.Pattern.compile("(?im)^Content-Length: ([0-9]+)\\r?$").matcher(partial.substring(0, end));
                    if (length.find() && bytes.size() - end - 4 >= Long.parseLong(length.group(1))) break;
                }
            }
            byte[] all = bytes.toByteArray();
            String text = new String(all, StandardCharsets.ISO_8859_1);
            int split = text.indexOf("\r\n\r\n");
            if (split < 0) throw new IOException("Invalid response: " + text);
            String[] lines = text.substring(0, split).split("\r\n");
            Map<String, String> headers = new HashMap<>();
            for (int i = 1; i < lines.length; i++) {
                int colon = lines[i].indexOf(':');
                headers.put(lines[i].substring(0, colon).toLowerCase(Locale.ROOT), lines[i].substring(colon + 1).trim());
            }
            return new Response(Integer.parseInt(lines[0].split(" ")[1]), headers, Arrays.copyOfRange(all, split + 4, all.length));
        }
    }
    private static String repeat(char c, int n) { char[] value = new char[n]; Arrays.fill(value, c); return new String(value); }
    private static void check(boolean condition, String label) { assertions++; if (!condition) throw new AssertionError(label); }
    private static void equal(Object expected, Object actual, String label) { check(expected.equals(actual), label + ": expected " + expected + ", got " + actual); }
    private static final class Response {
        final int status;
        final Map<String, String> headers;
        final byte[] body;
        Response(int status, Map<String, String> headers, byte[] body) { this.status = status; this.headers = headers; this.body = body; }
        String text() { return new String(body, StandardCharsets.UTF_8); }
    }
}
