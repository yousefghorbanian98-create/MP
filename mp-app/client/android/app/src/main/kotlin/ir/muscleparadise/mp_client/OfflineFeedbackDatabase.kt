package ir.muscleparadise.mp_client

import android.content.ContentValues
import android.content.Context
import android.database.Cursor
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

/** Private, owner-scoped SQLite outbox for structured set feedback only. */
internal class OfflineFeedbackDatabase(context: Context) :
    SQLiteOpenHelper(context.applicationContext, DATABASE_NAME, null, DATABASE_VERSION) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE sync_queue (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_member_id INTEGER NOT NULL,
              client_id TEXT NOT NULL,
              device_id TEXT NOT NULL,
              program_id INTEGER,
              movement_id TEXT NOT NULL,
              weight REAL NOT NULL,
              target_reps INTEGER NOT NULL,
              reps_done INTEGER NOT NULL,
              rir REAL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              status TEXT NOT NULL CHECK(status IN ('pending','retry','conflict','failed','synced')),
              attempts INTEGER NOT NULL DEFAULT 0,
              next_attempt_at TEXT,
              last_error_code TEXT,
              synced_at TEXT,
              UNIQUE(owner_member_id, device_id, client_id)
            )
            """.trimIndent(),
        )
        db.execSQL("CREATE INDEX sync_queue_owner_order ON sync_queue(owner_member_id, created_at, id)")
        db.execSQL("CREATE INDEX sync_queue_due ON sync_queue(owner_member_id, status, next_attempt_at)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // No local schema predates version 1. Future schema changes must add an
        // explicit, tested migration here; queued records are never dropped.
        if (oldVersion < 1) onCreate(db)
    }

    fun enqueue(args: Map<*, *>): Map<String, Any?> {
        requireOnlyKeys(
            args,
            setOf(
                "owner_member_id",
                "client_id",
                "device_id",
                "program_id",
                "movement_id",
                "weight",
                "target_reps",
                "reps_done",
                "rir",
                "created_at",
                "updated_at",
            ),
        )
        val ownerId = args.requiredLong("owner_member_id").also { require(it > 0) }
        val clientId = args.requiredString("client_id").also { require(it.length in 1..64) }
        val deviceId = args.requiredString("device_id").also { require(it.length in 1..64) }
        val programId = args.optionalLong("program_id")?.also { require(it > 0) }
        val movementId = args.requiredString("movement_id").also { require(it.length in 1..60) }
        val weight = args.requiredDouble("weight").also { require(it.isFinite() && it in 0.0..500.0) }
        val targetReps = args.requiredLong("target_reps").also { require(it in 0..200) }
        val repsDone = args.requiredLong("reps_done").also { require(it in 0..200) }
        val rir = args.optionalDouble("rir")?.also { require(it.isFinite() && it in 0.0..10.0) }
        val createdAt = args.requiredString("created_at").also { require(it.length in 1..40) }
        val updatedAt = args.requiredString("updated_at").also { require(it.length in 1..40) }

        val db = writableDatabase
        val existing = db.query(
            TABLE,
            null,
            "owner_member_id = ? AND device_id = ? AND client_id = ?",
            arrayOf(ownerId.toString(), deviceId, clientId),
            null,
            null,
            null,
            "1",
        ).use { cursor -> if (cursor.moveToFirst()) cursor.toRow() else null }
        if (existing != null) {
            val samePayload = existing["program_id"] == programId &&
                existing["movement_id"] == movementId &&
                existing["weight"] == weight &&
                existing["target_reps"] == targetReps &&
                existing["reps_done"] == repsDone &&
                existing["rir"] == rir &&
                existing["updated_at"] == updatedAt
            require(samePayload) { "Queue identity cannot be reused with changed data" }
            return existing
        }

        val values = ContentValues().apply {
            put("owner_member_id", ownerId)
            put("client_id", clientId)
            put("device_id", deviceId)
            if (programId == null) putNull("program_id") else put("program_id", programId)
            put("movement_id", movementId)
            put("weight", weight)
            put("target_reps", targetReps)
            put("reps_done", repsDone)
            if (rir == null) putNull("rir") else put("rir", rir)
            put("created_at", createdAt)
            put("updated_at", updatedAt)
            put("status", "pending")
            put("attempts", 0)
        }
        val id = db.insertOrThrow(TABLE, null, values)
        return findById(db, ownerId, id) ?: error("Inserted queue record was not readable")
    }

    fun listForOwner(ownerId: Long, limit: Int): List<Map<String, Any?>> {
        require(ownerId > 0)
        val safeLimit = limit.coerceIn(1, 500)
        return readableDatabase.query(
            TABLE,
            null,
            "owner_member_id = ?",
            arrayOf(ownerId.toString()),
            null,
            null,
            "CASE WHEN status = 'synced' THEN 1 ELSE 0 END ASC, created_at ASC, id ASC",
            safeLimit.toString(),
        ).use { cursor -> cursor.toRows() }
    }

    fun countUnresolved(ownerId: Long): Int {
        require(ownerId > 0)
        return readableDatabase.rawQuery(
            "SELECT COUNT(*) FROM $TABLE WHERE owner_member_id = ? AND status != 'synced'",
            arrayOf(ownerId.toString()),
        ).use { cursor -> if (cursor.moveToFirst()) cursor.getInt(0) else 0 }
    }

    fun listDue(ownerId: Long, now: String, limit: Int): List<Map<String, Any?>> {
        require(ownerId > 0 && now.length in 1..40)
        val safeLimit = limit.coerceIn(1, 100)
        return readableDatabase.query(
            TABLE,
            null,
            "owner_member_id = ? AND (status = 'pending' OR (status = 'retry' AND (next_attempt_at IS NULL OR next_attempt_at <= ?)))",
            arrayOf(ownerId.toString(), now),
            null,
            null,
            "created_at ASC, id ASC",
            safeLimit.toString(),
        ).use { cursor -> cursor.toRows() }
    }

    fun markSynced(ownerId: Long, id: Long, syncedAt: String) {
        require(ownerId > 0 && id > 0 && syncedAt.length in 1..40)
        val values = ContentValues().apply {
            put("status", "synced")
            put("synced_at", syncedAt)
            putNull("next_attempt_at")
            putNull("last_error_code")
        }
        updateActive(ownerId, id, values)
    }

    fun markConflict(ownerId: Long, id: Long, errorCode: String) {
        require(ownerId > 0 && id > 0)
        require(errorCode in ERROR_CODES)
        val values = ContentValues().apply {
            put("status", "conflict")
            put("last_error_code", errorCode)
            putNull("next_attempt_at")
        }
        updateActive(ownerId, id, values)
    }

    fun markRetry(ownerId: Long, id: Long, errorCode: String, nextAttemptAt: String, maxAttempts: Int) {
        require(ownerId > 0 && id > 0 && maxAttempts in 1..10)
        require(errorCode in ERROR_CODES && nextAttemptAt.length in 1..40)
        val current = findById(readableDatabase, ownerId, id) ?: error("Queue item not found")
        require(current["status"] == "pending" || current["status"] == "retry")
        val attempts = (current["attempts"] as Number).toInt() + 1
        val exhausted = attempts >= maxAttempts
        val values = ContentValues().apply {
            put("attempts", attempts)
            put("status", if (exhausted) "failed" else "retry")
            put("last_error_code", errorCode)
            if (exhausted) putNull("next_attempt_at") else put("next_attempt_at", nextAttemptAt)
        }
        updateActive(ownerId, id, values)
    }

    fun manualRetry(ownerId: Long, id: Long) {
        require(ownerId > 0 && id > 0)
        val values = ContentValues().apply {
            put("status", "pending")
            put("attempts", 0)
            putNull("next_attempt_at")
            putNull("last_error_code")
        }
        val changed = writableDatabase.update(
            TABLE,
            values,
            "id = ? AND owner_member_id = ? AND status = 'failed'",
            arrayOf(id.toString(), ownerId.toString()),
        )
        require(changed == 1) { "Only an owner's failed item can be retried manually" }
    }

    fun discardOwner(ownerId: Long): Int {
        require(ownerId > 0)
        return writableDatabase.delete(TABLE, "owner_member_id = ?", arrayOf(ownerId.toString()))
    }

    private fun updateActive(ownerId: Long, id: Long, values: ContentValues) {
        val changed = writableDatabase.update(
            TABLE,
            values,
            "id = ? AND owner_member_id = ? AND status IN ('pending','retry')",
            arrayOf(id.toString(), ownerId.toString()),
        )
        require(changed == 1) { "Queue item is missing, belongs to another owner, or is terminal" }
    }

    private fun findById(db: SQLiteDatabase, ownerId: Long, id: Long): Map<String, Any?>? =
        db.query(
            TABLE,
            null,
            "id = ? AND owner_member_id = ?",
            arrayOf(id.toString(), ownerId.toString()),
            null,
            null,
            null,
            "1",
        ).use { cursor -> if (cursor.moveToFirst()) cursor.toRow() else null }

    private fun requireOnlyKeys(args: Map<*, *>, allowed: Set<String>) {
        require(args.keys.all { it is String && it in allowed })
    }

    private fun Map<*, *>.requiredString(key: String): String = this[key] as? String ?: error("Invalid field")

    private fun Map<*, *>.requiredLong(key: String): Long = (this[key] as? Number)?.toLong() ?: error("Invalid field")

    private fun Map<*, *>.optionalLong(key: String): Long? {
        val value = this[key] ?: return null
        return (value as? Number)?.toLong() ?: error("Invalid field")
    }

    private fun Map<*, *>.requiredDouble(key: String): Double = (this[key] as? Number)?.toDouble() ?: error("Invalid field")

    private fun Map<*, *>.optionalDouble(key: String): Double? {
        val value = this[key] ?: return null
        return (value as? Number)?.toDouble() ?: error("Invalid field")
    }

    private fun Cursor.toRows(): List<Map<String, Any?>> {
        val rows = mutableListOf<Map<String, Any?>>()
        while (moveToNext()) rows += toRow()
        return rows
    }

    private fun Cursor.toRow(): Map<String, Any?> {
        fun long(name: String): Long? {
            val column = getColumnIndexOrThrow(name)
            return if (isNull(column)) null else getLong(column)
        }
        fun double(name: String): Double? {
            val column = getColumnIndexOrThrow(name)
            return if (isNull(column)) null else getDouble(column)
        }
        fun string(name: String): String? {
            val column = getColumnIndexOrThrow(name)
            return if (isNull(column)) null else getString(column)
        }
        return linkedMapOf(
            "id" to long("id"),
            "owner_member_id" to long("owner_member_id"),
            "client_id" to string("client_id"),
            "device_id" to string("device_id"),
            "program_id" to long("program_id"),
            "movement_id" to string("movement_id"),
            "weight" to double("weight"),
            "target_reps" to long("target_reps"),
            "reps_done" to long("reps_done"),
            "rir" to double("rir"),
            "created_at" to string("created_at"),
            "updated_at" to string("updated_at"),
            "status" to string("status"),
            "attempts" to long("attempts"),
            "next_attempt_at" to string("next_attempt_at"),
            "last_error_code" to string("last_error_code"),
            "synced_at" to string("synced_at"),
        )
    }

    private companion object {
        const val DATABASE_NAME = "mp_offline_feedback.db"
        const val DATABASE_VERSION = 1
        const val TABLE = "sync_queue"
        val ERROR_CODES = setOf(
            "network",
            "server_5xx",
            "server_rejected",
            "server_stale",
            "clock_skew",
            "auth_required",
            "invalid_response",
        )
    }
}
