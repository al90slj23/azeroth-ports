package io.github.al90slj23.azerothsurvivors;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Keeps loopback assets available while Chrome runs the game in its own process. */
public final class GameService extends Service {
    public static final int PORT = 47615;
    public static final String ORIGIN = "http://127.0.0.1:" + PORT;
    public static final String ACTION_STOP = "io.github.al90slj23.azerothsurvivors.STOP";
    public static volatile boolean ready;
    public static volatile String failure;

    private static final String CHANNEL = "local_game";
    private static final int NOTIFICATION_ID = 47615;
    private final Object stateLock = new Object();
    private final ExecutorService worker = Executors.newSingleThreadExecutor(task -> {
        Thread thread = new Thread(task, "azeroth-local-assets");
        thread.setDaemon(true);
        return thread;
    });
    private LocalHttpServer server;
    private boolean starting;
    private boolean stopping;

    @Override
    public void onCreate() {
        super.onCreate();
        ready = false;
        failure = null;
        NotificationManager manager = getSystemService(NotificationManager.class);
        NotificationChannel channel = new NotificationChannel(
                CHANNEL, "本地游戏资源", NotificationManager.IMPORTANCE_LOW);
        channel.setDescription("游戏运行时提供安装包内的地图、模型及声音资源");
        channel.setSound(null, null);
        manager.createNotificationChannel(channel);

        Intent main = new Intent(this, MainActivity.class)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent open = PendingIntent.getActivity(this, 0, main,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent stop = PendingIntent.getService(this, 1,
                new Intent(this, GameService.class).setAction(ACTION_STOP),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification notification = new Notification.Builder(this, CHANNEL)
                .setSmallIcon(android.R.drawable.ic_media_play)
                .setContentTitle("艾泽拉斯幸存者")
                .setContentText("本地游戏资源服务运行中")
                .setContentIntent(open)
                .setCategory(Notification.CATEGORY_SERVICE)
                .setOngoing(true)
                .setOnlyAlertOnce(true)
                .addAction(new Notification.Action.Builder(
                        android.R.drawable.ic_media_pause, "停止游戏", stop).build())
                .build();
        // Foreground immediately, before reading the large package index or opening sockets.
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIFICATION_ID, notification,
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null && ACTION_STOP.equals(intent.getAction())) {
            shutdown();
            stopForeground(STOP_FOREGROUND_REMOVE);
            stopSelf();
            return START_NOT_STICKY;
        }
        synchronized (stateLock) {
            if (stopping) return START_NOT_STICKY;
            if (starting || server != null) return START_STICKY;
            starting = true;
        }
        worker.execute(() -> {
            LocalHttpServer candidate = null;
            try {
                AssetSource source = new AssetSource(getAssets());
                candidate = new LocalHttpServer(PORT, source);
                synchronized (stateLock) {
                    if (stopping) {
                        closeQuietly(candidate);
                        return;
                    }
                    candidate.start();
                    server = candidate;
                    starting = false;
                    ready = true;
                }
            } catch (Exception error) {
                closeQuietly(candidate);
                synchronized (stateLock) {
                    starting = false;
                    ready = false;
                    if (!stopping) {
                        failure = "无法启动本地游戏资源，请关闭其他游戏实例后重试。";
                        Log.e("AzerothAssets", "Local asset service failed", error);
                    }
                }
                stopSelf();
            }
        });
        return START_STICKY;
    }

    private void shutdown() {
        LocalHttpServer previous;
        synchronized (stateLock) {
            stopping = true;
            starting = false;
            ready = false;
            previous = server;
            server = null;
        }
        worker.shutdownNow();
        closeQuietly(previous);
    }

    private static void closeQuietly(LocalHttpServer value) {
        if (value == null) return;
        try {
            value.close();
        } catch (Exception error) {
            Log.w("AzerothAssets", "Could not close local asset service", error);
        }
    }

    @Override
    public void onDestroy() {
        shutdown();
        stopForeground(STOP_FOREGROUND_REMOVE);
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
