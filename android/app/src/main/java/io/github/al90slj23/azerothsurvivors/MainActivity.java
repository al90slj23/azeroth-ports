package io.github.al90slj23.azerothsurvivors;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Insets;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.WindowInsets;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

/** The launcher owns no save files; each renderer retains its own origin storage. */
public final class MainActivity extends Activity {
    private static final int GOLD = 0xffedc96a;
    private Boolean pendingChrome;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        getWindow().setDecorFitsSystemWindows(false);
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(0xff10100d);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setGravity(Gravity.CENTER);
        body.setPadding(dp(28), dp(28), dp(28), dp(28));
        body.setOnApplyWindowInsetsListener((v, insets) -> {
            Insets bars = insets.getInsets(WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout());
            v.setPadding(dp(28) + bars.left, dp(28) + bars.top, dp(28) + bars.right, dp(28) + bars.bottom);
            return insets;
        });
        scroll.addView(body);
        title(body, "AZEROTH\nSURVIVORS", 32, GOLD);
        title(body, "艾泽拉斯幸存者", 20, 0xffeee2be);
        TextView info = title(body, "安卓社区移植版\n内置游戏资源 · 中文界面 · 原版合作模式", 14, 0xffaaa48f);
        info.setPadding(0, dp(12), 0, dp(22));
        button(body, "开始游戏", () -> begin(false));
        button(body, "使用 Chrome 模式", () -> begin(true));
        button(body, "停止游戏资源服务", () -> {
            stopService(new Intent(this, GameService.class));
            android.widget.Toast.makeText(this, "资源服务已停止", android.widget.Toast.LENGTH_SHORT).show();
        });
        button(body, "兼容与存档说明", () -> new AlertDialog.Builder(this)
                .setTitle("开始之前")
                .setMessage("适用于 Android 12 及以上设备。图形能力取决于手机 GPU、驱动和渲染内核，请更新 Android System WebView 与 Chrome。\n\n内置模式会先检测 WebGPU。若无法启动，可使用 Chrome 模式；首次触控后游戏会尝试全屏和横屏。\n\n两种模式的存档各自保存。切换模式前，请在游戏的选项 → Saves 中导出存档，再在另一模式导入。\n\n合作需要联网，所有玩家应使用相同游戏版本。Chrome 模式运行时，请保留资源服务通知；退出后可在这里或通知中停止。\n\n游戏由 Aethus 制作，本移植并非官方发行。")
                .setPositiveButton("知道了", null).show());
        TextView footer = title(body, "Aethus 原作 · Android 社区封装\n游戏画面和运算均在你的设备上执行", 12, 0xff77776d);
        footer.setPadding(0, dp(20), 0, 0);
        setContentView(scroll);
    }

    private void begin(boolean chrome) {
        if (Build.VERSION.SDK_INT >= 33 && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            pendingChrome = chrome;
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 10);
            return;
        }
        launch(chrome);
    }

    private void launch(boolean chrome) {
        startActivity(new Intent(this, GameActivity.class).putExtra(GameActivity.EXTRA_CHROME, chrome));
    }

    @Override public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(requestCode, permissions, results);
        if (requestCode == 10 && pendingChrome != null) {
            boolean chrome = pendingChrome;
            pendingChrome = null;
            // Android permits the foreground service even when its notification is declined.
            launch(chrome);
        }
    }

    private TextView title(LinearLayout body, String text, int size, int color) {
        TextView view = new TextView(this);
        view.setText(text); view.setTextSize(size); view.setTextColor(color);
        view.setGravity(Gravity.CENTER); view.setTypeface(Typeface.create("serif", Typeface.NORMAL));
        body.addView(view, new LinearLayout.LayoutParams(-1, -2));
        return view;
    }

    private void button(LinearLayout body, String label, Runnable action) {
        Button button = new Button(this);
        button.setAllCaps(false); button.setText(label); button.setTextColor(GOLD); button.setTextSize(16);
        GradientDrawable background = new GradientDrawable();
        background.setColor(0xff24180e); background.setCornerRadius(dp(8)); background.setStroke(dp(1), 0xff8f7338);
        button.setBackground(background);
        LinearLayout.LayoutParams layout = new LinearLayout.LayoutParams(-1, dp(52));
        layout.setMargins(0, dp(6), 0, dp(6));
        body.addView(button, layout); button.setOnClickListener(v -> action.run());
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
