package ir.muscleparadise.mp_client

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Handler
import android.os.Looper
import io.flutter.embedding.android.FlutterFragmentActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import java.util.concurrent.Executors

class MainActivity : FlutterFragmentActivity() {
    private val offlineExecutor = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private lateinit var offlineDatabase: OfflineFeedbackDatabase

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        offlineDatabase = OfflineFeedbackDatabase(applicationContext)
        MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            OFFLINE_FEEDBACK_CHANNEL,
        ).setMethodCallHandler { call, result ->
            if (call.method == "hasInternetNetwork") {
                result.success(hasInternetNetwork())
                return@setMethodCallHandler
            }

            offlineExecutor.execute {
                try {
                    val value = handleOfflineFeedbackCall(call)
                    mainHandler.post { result.success(value) }
                } catch (_: Exception) {
                    // Do not log request payloads or local fitness data.
                    mainHandler.post {
                        result.error("offline_store_error", "Offline feedback storage operation failed", null)
                    }
                }
            }
        }
    }

    private fun hasInternetNetwork(): Boolean {
        val manager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = manager.activeNetwork ?: return false
        val capabilities = manager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun handleOfflineFeedbackCall(call: MethodCall): Any? {
        val args = call.arguments as? Map<*, *> ?: emptyMap<Any, Any>()
        return when (call.method) {
            "enqueue" -> offlineDatabase.enqueue(args)
            "listForOwner" -> offlineDatabase.listForOwner(
                args.long("owner_member_id"),
                args.longOrDefault("limit", 100).toInt(),
            )
            "countUnresolved" -> offlineDatabase.countUnresolved(args.long("owner_member_id"))
            "listDue" -> offlineDatabase.listDue(
                args.long("owner_member_id"),
                args.string("now"),
                args.longOrDefault("limit", 100).toInt(),
            )
            "markSynced" -> {
                offlineDatabase.markSynced(
                    args.long("owner_member_id"),
                    args.long("id"),
                    args.string("synced_at"),
                )
                true
            }
            "markConflict" -> {
                offlineDatabase.markConflict(
                    args.long("owner_member_id"),
                    args.long("id"),
                    args.string("error_code"),
                )
                true
            }
            "markRetry" -> {
                offlineDatabase.markRetry(
                    args.long("owner_member_id"),
                    args.long("id"),
                    args.string("error_code"),
                    args.string("next_attempt_at"),
                    args.longOrDefault("max_attempts", 5).toInt(),
                )
                true
            }
            "manualRetry" -> {
                offlineDatabase.manualRetry(args.long("owner_member_id"), args.long("id"))
                true
            }
            "discardOwner" -> offlineDatabase.discardOwner(args.long("owner_member_id"))
            else -> throw IllegalArgumentException("Unsupported offline feedback method")
        }
    }

    private fun Map<*, *>.long(key: String): Long =
        (this[key] as? Number)?.toLong() ?: throw IllegalArgumentException("Invalid numeric argument")

    private fun Map<*, *>.longOrDefault(key: String, defaultValue: Long): Long =
        (this[key] as? Number)?.toLong() ?: defaultValue

    private fun Map<*, *>.string(key: String): String =
        this[key] as? String ?: throw IllegalArgumentException("Invalid string argument")

    override fun onDestroy() {
        offlineExecutor.shutdown()
        if (::offlineDatabase.isInitialized) offlineDatabase.close()
        super.onDestroy()
    }

    private companion object {
        const val OFFLINE_FEEDBACK_CHANNEL = "ir.muscleparadise.mp_client/offline_feedback"
    }
}
