package io.github.al90slj23.azerothsurvivors;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.util.Base64;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.JavascriptInterface;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** A local-origin game view. Native bridge capabilities are limited to GPU probing and save export. */
public final class GameActivity extends Activity {
    public static final String EXTRA_CHROME = "chrome_mode";
    private static final int PICK_FILE = 20;
    private static final int EXPORT_SAVE = 21;
    private static final int MAX_SAVE_BYTES = 8 * 1024 * 1024;
    private static final String PROBE_URL = GameService.ORIGIN + "/android-probe.html";
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService saveExecutor = Executors.newSingleThreadExecutor();
    private FrameLayout container;
    private TextView status;
    private WebView web;
    private View fullScreenView;
    private WebChromeClient.CustomViewCallback fullScreenCallback;
    private ValueCallback<Uri[]> fileCallback;
    private byte[] pendingSave;
    private boolean preparingSave;
    private boolean probing;
    private boolean worldLoaded;
    private boolean externalSession;
    private boolean dialogShown;
    private long serverDeadline;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
        getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        container = new FrameLayout(this); container.setBackgroundColor(Color.BLACK);
        status = new TextView(this); status.setTextColor(0xffedc96a); status.setTextSize(18);
        status.setGravity(Gravity.CENTER); status.setText("正在准备本地游戏资源…");
        container.addView(status, new FrameLayout.LayoutParams(-1, -1));
        setContentView(container); immersive();
        if (android.os.Build.VERSION.SDK_INT >= 33) {
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    android.window.OnBackInvokedDispatcher.PRIORITY_DEFAULT, this::onBackPressed);
        }
        if (!GameService.ready) GameService.failure = null;
        startForegroundService(new Intent(this, GameService.class));
        serverDeadline = SystemClock.elapsedRealtime() + 15000;
        handler.postDelayed(this::waitForServer, 150);
    }

    private void waitForServer() {
        if (isFinishing() || isDestroyed()) return;
        if (GameService.ready) {
            if (getIntent().getBooleanExtra(EXTRA_CHROME, false)) startChrome();
            else createGameView();
        } else if (GameService.failure != null) {
            fail("无法启动本地游戏资源服务。请停止服务后重试。\n" + GameService.failure);
        } else if (SystemClock.elapsedRealtime() > serverDeadline) {
            fail("准备资源超时，请返回后重试。");
        } else handler.postDelayed(this::waitForServer, 150);
    }

    private void startChrome() {
        if (SessionLauncher.openGame(this)) {
            externalSession = true;
            finish();
        } else {
            fail("Chrome 模式需要安装最新版 Chrome。你也可以返回尝试内置模式。");
        }
    }

    private void createGameView() {
        if (web != null) return;
        web = new WebView(this);
        web.setBackgroundColor(Color.BLACK);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setLongClickable(false);
        web.setOnLongClickListener(v -> true);
        web.addJavascriptInterface(new AndroidHost(), "AndroidHost");
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                if (!request.isForMainFrame()) return !isLocal(request.getUrl());
                if (isLocal(request.getUrl())) return false;
                SessionLauncher.openOfficial(GameActivity.this, request.getUrl());
                return true;
            }
            @Override public void onPageFinished(WebView view, String url) {
                if (isLocal(Uri.parse(url)) && !PROBE_URL.equals(url) && worldLoaded) status.setVisibility(View.GONE);
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    fail("游戏页面无法载入，请返回重试或尝试 Chrome 模式。");
                }
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onShowCustomView(View view, CustomViewCallback callback) {
                if (fullScreenView != null) { callback.onCustomViewHidden(); return; }
                fullScreenView = view; fullScreenCallback = callback;
                web.setVisibility(View.GONE);
                container.addView(view, new FrameLayout.LayoutParams(-1, -1));
                immersive();
            }
            @Override public void onHideCustomView() { hideFullScreen(); }
            @Override public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (!localPageActive() || probing || !worldLoaded) {
                    callback.onReceiveValue(null);
                    return true;
                }
                if (!localPageActive()) { callback.onReceiveValue(null); return true; }
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType("*/*");
                pick.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE);
                try { startActivityForResult(pick, PICK_FILE); }
                catch (ActivityNotFoundException error) {
                    fileCallback.onReceiveValue(null); fileCallback = null;
                    Toast.makeText(GameActivity.this, "系统未提供文件选择器", Toast.LENGTH_LONG).show();
                }
                return true;
            }
        });
        container.addView(web, 0, new FrameLayout.LayoutParams(-1, -1));
        status.setText("正在检查图形支持…");
        probing = true;
        web.loadUrl(PROBE_URL);
        handler.postDelayed(() -> {
            if (probing && !isFinishing() && !isDestroyed()) {
                probing = false;
                offerChrome("内置图形检测未能完成。请更新 Android System WebView，或尝试 Chrome 模式。");
            }
        }, 12000);
    }

    static boolean isLocal(Uri uri) {
        return uri != null && "http".equalsIgnoreCase(uri.getScheme())
                && "127.0.0.1".equals(uri.getHost()) && uri.getPort() == GameService.PORT
                && uri.getUserInfo() == null;
    }

    private boolean localPageActive() {
        return web != null && web.getUrl() != null && isLocal(Uri.parse(web.getUrl()));
    }

    public final class AndroidHost {
        @JavascriptInterface public void reportGpu(boolean available, String reason) {
            runOnUiThread(() -> {
                if (!probing || web == null || !PROBE_URL.equals(web.getUrl()) || isFinishing()) return;
                probing = false;
                if (!available) {
                    offerChrome("当前内置渲染内核没有可用的 WebGPU 图形适配器。请更新系统组件，或使用 Chrome 模式。");
                    return;
                }
                worldLoaded = true;
                status.setText("正在载入游戏…");
                web.loadUrl(GameService.ORIGIN + "/");
            });
        }

        @JavascriptInterface public void exportSave(String filename, String encoded) {
            runOnUiThread(() -> {
                if (!localPageActive() || probing || !worldLoaded || isFinishing() || isDestroyed()
                        || preparingSave || pendingSave != null) return;
                if (encoded == null || encoded.length() > ((MAX_SAVE_BYTES + 2L) / 3L) * 4L + 32L) {
                    toast("存档过大，无法导出"); return;
                }
                preparingSave = true;
                saveExecutor.execute(() -> {
                    byte[] decoded;
                    try {
                        decoded = Base64.decode(encoded, Base64.NO_WRAP);
                        if (decoded.length > MAX_SAVE_BYTES || decoded.length < 5
                                || !"RSE1:".equals(new String(decoded, 0, 5, StandardCharsets.US_ASCII))) {
                            throw new IllegalArgumentException("Invalid sealed save");
                        }
                    } catch (IllegalArgumentException error) {
                        runOnUiThread(() -> { preparingSave = false; toast("无法识别此游戏存档"); });
                        return;
                    }
                    runOnUiThread(() -> {
                        preparingSave = false;
                        if (isFinishing() || isDestroyed() || !localPageActive()) return;
                        pendingSave = decoded;
                        String safe = filename == null ? "AzerothSurvivors.sav" : filename.replaceAll("[^A-Za-z0-9._ -]", "_");
                        if (safe.length() > 100) safe = safe.substring(0, 96) + ".sav";
                        if (!safe.endsWith(".sav")) safe += ".sav";
                        Intent save = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                                .setType("application/octet-stream").putExtra(Intent.EXTRA_TITLE, safe);
                        try { startActivityForResult(save, EXPORT_SAVE); }
                        catch (ActivityNotFoundException error) { pendingSave = null; toast("系统未提供存档保存器"); }
                    });
                });
            });
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == PICK_FILE && fileCallback != null) {
            Uri[] result = null;
            if (resultCode == RESULT_OK && data != null) {
                if (data.getClipData() != null) {
                    result = new Uri[data.getClipData().getItemCount()];
                    for (int i = 0; i < result.length; i++) result[i] = data.getClipData().getItemAt(i).getUri();
                } else if (data.getData() != null) result = new Uri[]{data.getData()};
            }
            fileCallback.onReceiveValue(result); fileCallback = null;
        } else if (requestCode == EXPORT_SAVE) {
            byte[] bytes = pendingSave; pendingSave = null;
            Uri destination = data == null ? null : data.getData();
            if (resultCode != RESULT_OK || bytes == null || destination == null) return;
            if (!"content".equals(destination.getScheme())) { toast("不支持此存档位置"); return; }
            saveExecutor.execute(() -> {
                try (OutputStream output = getContentResolver().openOutputStream(destination, "wt")) {
                    if (output == null) throw new IOException("No document stream");
                    output.write(bytes); output.flush();
                    runOnUiThread(() -> toast("存档已导出"));
                } catch (IOException | SecurityException error) {
                    runOnUiThread(() -> toast("存档保存失败，请重新导出"));
                }
            });
        }
    }

    private void offerChrome(String message) {
        status.setVisibility(View.VISIBLE); status.setText(message);
        if (dialogShown || isFinishing() || isDestroyed()) return;
        dialogShown = true;
        new AlertDialog.Builder(this).setTitle("图形兼容模式").setMessage(message
                + "\n\nChrome 模式与内置模式的存档独立，可通过游戏内导出／导入迁移。")
                .setPositiveButton("使用 Chrome", (d, w) -> { dialogShown = false; startChrome(); })
                .setNegativeButton("返回", (d, w) -> finish())
                .setOnCancelListener(d -> { dialogShown = false; finish(); }).show();
    }

    private void fail(String message) {
        if (dialogShown || isFinishing() || isDestroyed()) return;
        dialogShown = true;
        status.setVisibility(View.VISIBLE); status.setText(message);
        new AlertDialog.Builder(this).setTitle("游戏未能启动").setMessage(message)
                .setPositiveButton("返回", (d, w) -> finish())
                .setOnCancelListener(d -> finish()).show();
    }

    private void hideFullScreen() {
        if (fullScreenView == null) return;
        container.removeView(fullScreenView); fullScreenView = null;
        if (web != null) web.setVisibility(View.VISIBLE);
        WebChromeClient.CustomViewCallback callback = fullScreenCallback; fullScreenCallback = null;
        if (callback != null) callback.onCustomViewHidden();
        immersive();
    }

    private void immersive() {
        getWindow().setDecorFitsSystemWindows(false);
        WindowInsetsController controller = getWindow().getInsetsController();
        if (controller != null) {
            controller.hide(WindowInsets.Type.systemBars());
            controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
        }
    }

    private void toast(String text) { if (!isDestroyed()) Toast.makeText(this, text, Toast.LENGTH_LONG).show(); }

    @Override public void onBackPressed() {
        if (fullScreenView != null) { hideFullScreen(); return; }
        if (!worldLoaded) { finish(); return; }
        new AlertDialog.Builder(this).setTitle("返回启动页？")
                .setMessage("已保存的进度会保留，当前冒险将结束。")
                .setPositiveButton("返回", (d, w) -> finish()).setNegativeButton("继续游戏", null).show();
    }

    @Override protected void onPause() { if (web != null) web.onPause(); super.onPause(); }
    @Override protected void onResume() { super.onResume(); if (web != null) web.onResume(); immersive(); }
    @Override public void onWindowFocusChanged(boolean focus) { super.onWindowFocusChanged(focus); if (focus) immersive(); }

    @Override protected void onDestroy() {
        handler.removeCallbacksAndMessages(null);
        if (fileCallback != null) { fileCallback.onReceiveValue(null); fileCallback = null; }
        if (web != null) {
            web.removeJavascriptInterface("AndroidHost"); web.stopLoading();
            if (web.getParent() instanceof ViewGroup) ((ViewGroup) web.getParent()).removeView(web);
            web.destroy(); web = null;
        }
        if (isFinishing() && !externalSession && !isChangingConfigurations()) stopService(new Intent(this, GameService.class));
        saveExecutor.shutdown();
        super.onDestroy();
    }
}
