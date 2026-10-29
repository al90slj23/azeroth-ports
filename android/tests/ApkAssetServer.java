import io.github.al90slj23.azerothsurvivors.LocalHttpServer;
import java.io.InputStream;
import java.io.IOException;
import java.io.FileNotFoundException;
import java.util.zip.ZipFile;
import java.util.zip.ZipEntry;

/** Exercises the actual signed APK's compressed assets through the production HTTP server. */
public final class ApkAssetServer {
    public static void main(String[] args) throws Exception {
        final ZipFile zip = new ZipFile(args[0]);
        LocalHttpServer.Source source = new LocalHttpServer.Source() {
            private ZipEntry entry(String path) throws IOException {
                ZipEntry entry = zip.getEntry("assets/www/" + path);
                if (entry == null) throw new FileNotFoundException(path);
                return entry;
            }
            public InputStream open(String path) throws IOException { return zip.getInputStream(entry(path)); }
            public long length(String path) throws IOException { return entry(path).getSize(); }
            public String revision() { return "android-apk-smoke"; }
        };
        final LocalHttpServer server = new LocalHttpServer(Integer.parseInt(args[1]), source);
        server.start();
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            server.close();
            try { zip.close(); } catch (IOException ignored) { }
        }));
        System.out.println("APK assets on http://127.0.0.1:" + server.getPort());
        Thread.currentThread().join();
    }
}
