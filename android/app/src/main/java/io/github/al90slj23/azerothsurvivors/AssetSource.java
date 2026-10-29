package io.github.al90slj23.azerothsurvivors;

import android.content.res.AssetManager;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;

/** Streams bundled assets directly from the APK, including compressed ZIP entries. */
public final class AssetSource implements LocalHttpServer.Source {
    private static final int MAX_INDEX_BYTES = 16 * 1024 * 1024;
    private final AssetManager assets;
    private final Map<String, Long> lengths;

    public AssetSource(AssetManager assets) throws IOException {
        this.assets = assets;
        Map<String, Long> entries = new HashMap<>();
        try (InputStream in = assets.open("android-asset-index.json", AssetManager.ACCESS_STREAMING)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[16 * 1024];
            int count;
            while ((count = in.read(buffer)) != -1) {
                if (out.size() + count > MAX_INDEX_BYTES) {
                    throw new IOException("Bundled asset index is too large");
                }
                out.write(buffer, 0, count);
            }
            JSONObject index = new JSONObject(new String(out.toByteArray(), StandardCharsets.UTF_8));
            Iterator<String> names = index.keys();
            while (names.hasNext()) {
                String name = names.next();
                validatePath(name);
                Object value = index.get(name);
                if (!(value instanceof Number)) {
                    throw new IOException("Invalid size in bundled asset index");
                }
                long length = ((Number) value).longValue();
                if (length < 0 || ((Number) value).doubleValue() != (double) length) {
                    throw new IOException("Invalid size in bundled asset index");
                }
                entries.put(name, length);
            }
        } catch (JSONException error) {
            throw new IOException("Bundled asset index is invalid", error);
        }
        if (!entries.containsKey("index.html") || !entries.containsKey("wenilla_bg.wasm")
                || !entries.containsKey("android-probe.html")) {
            throw new IOException("Required bundled game assets are missing");
        }
        lengths = Collections.unmodifiableMap(entries);
    }

    @Override
    public String revision() {
        return BuildInfo.ASSET_REVISION;
    }

    @Override
    public InputStream open(String path) throws IOException {
        length(path); // An asset must be named explicitly in the signed package index.
        return assets.open("www/" + path, AssetManager.ACCESS_STREAMING);
    }

    @Override
    public long length(String path) throws IOException {
        validatePath(path);
        Long value = lengths.get(path);
        if (value == null) throw new FileNotFoundException("Asset not found");
        return value;
    }

    private static void validatePath(String path) throws IOException {
        if (path == null || path.isEmpty() || path.startsWith("/") || path.indexOf('\\') >= 0
                || path.indexOf('\0') >= 0 || path.indexOf('?') >= 0 || path.indexOf('#') >= 0) {
            throw new FileNotFoundException("Invalid asset path");
        }
        for (String part : path.split("/", -1)) {
            if (part.isEmpty() || part.equals(".") || part.equals("..")) {
                throw new FileNotFoundException("Invalid asset path");
            }
        }
    }
}
