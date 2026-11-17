/// صندوق اعلان واقعی عضو؛ unread از read_at و وضعیت از API می‌آید (M75).
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/app_state.dart';
import '../../core/membership.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

class NotificationsPage extends ConsumerStatefulWidget {
  const NotificationsPage({super.key});

  @override
  ConsumerState<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends ConsumerState<NotificationsPage> {
  final Set<int> _busyIds = {};
  String? _message;

  Future<void> _markRead(int notificationId) async {
    if (_busyIds.contains(notificationId)) return;
    setState(() => _busyIds.add(notificationId));
    try {
      await ref.read(apiClientProvider).post('/notifications/$notificationId/read', {});
      if (!mounted) return;
      setState(() => _message = 'اعلان به‌عنوان خوانده‌شده ثبت شد');
      ref.invalidate(myNotificationsProvider);
    } catch (error) {
      if (!mounted) return;
      setState(() => _message = 'خواندن اعلان ناموفق بود: $error');
      // اگر درخواست در سرور اعمال شده ولی پاسخ گم شده، وضعیت را دوباره بخوان.
      ref.invalidate(myNotificationsProvider);
    } finally {
      if (mounted) setState(() => _busyIds.remove(notificationId));
    }
  }

  @override
  Widget build(BuildContext context) {
    final notifications = ref.watch(myNotificationsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('اعلان‌ها'),
        backgroundColor: MpColors.background,
        surfaceTintColor: Colors.transparent,
      ),
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: () async => ref.invalidate(myNotificationsProvider),
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (_message != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Text(_message!, style: const TextStyle(color: MpColors.primaryLight)),
                ),
              notifications.when(
                loading: () => const GlassCard(
                  child: Padding(
                    padding: EdgeInsets.all(28),
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ),
                error: (error, _) => GlassCard(
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline, color: MpColors.danger, size: 36),
                      const SizedBox(height: 8),
                      Text('دریافت اعلان‌ها ناموفق بود: $error', textAlign: TextAlign.center),
                      const SizedBox(height: 8),
                      OutlinedButton(
                        onPressed: () => ref.invalidate(myNotificationsProvider),
                        child: const Text('تلاش دوباره'),
                      ),
                    ],
                  ),
                ),
                data: (rows) {
                  final unreadCount = rows.where((row) => row['read_at'] == null).length;
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      GlassCard(
                        child: Row(
                          children: [
                            const Icon(Icons.notifications_active_outlined,
                                color: MpColors.primary, size: 28),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                unreadCount == 0
                                    ? 'همهٔ اعلان‌ها خوانده شده‌اند'
                                    : '${_toPersianDigits('$unreadCount')} اعلان خوانده‌نشده',
                                style: const TextStyle(fontWeight: FontWeight.w700),
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      if (rows.isEmpty)
                        const GlassCard(
                          child: Padding(
                            padding: EdgeInsets.symmetric(vertical: 28, horizontal: 12),
                            child: Column(
                              children: [
                                Icon(Icons.notifications_none, size: 38, color: MpColors.textSecondary),
                                SizedBox(height: 8),
                                Text('اعلانی ندارید', textAlign: TextAlign.center),
                              ],
                            ),
                          ),
                        )
                      else
                        for (final row in rows) _NotificationTile(
                          notification: row,
                          isBusy: _busyIds.contains((row['id'] as num).toInt()),
                          onMarkRead: _markRead,
                        ),
                    ],
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _NotificationTile extends StatelessWidget {
  const _NotificationTile({
    required this.notification,
    required this.isBusy,
    required this.onMarkRead,
  });

  final Map<String, dynamic> notification;
  final bool isBusy;
  final ValueChanged<int> onMarkRead;

  @override
  Widget build(BuildContext context) {
    final id = (notification['id'] as num).toInt();
    final unread = notification['read_at'] == null;
    final title = notification['title'] as String;
    final body = notification['body'] is String ? notification['body'] as String : '';
    final createdAt = DateTime.parse(notification['created_at'] as String).toLocal();
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassCard(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              unread ? Icons.markunread_outlined : Icons.drafts_outlined,
              color: unread ? MpColors.primary : MpColors.textSecondary,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
                  if (body.isNotEmpty) ...[
                    const SizedBox(height: 5),
                    Text(body, style: TextStyle(color: MpColors.textSecondary, height: 1.5)),
                  ],
                  const SizedBox(height: 7),
                  Text(
                    '${unread ? 'خوانده‌نشده' : 'خوانده‌شده'} · ${formatJalaliDate(createdAt)}',
                    style: TextStyle(
                      fontSize: 11,
                      color: unread ? MpColors.primaryLight : MpColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            if (unread)
              IconButton(
                tooltip: 'علامت‌گذاری به‌عنوان خوانده‌شده',
                onPressed: isBusy ? null : () => onMarkRead(id),
                icon: isBusy
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.done, color: MpColors.primary),
              ),
          ],
        ),
      ),
    );
  }
}

String _toPersianDigits(String value) => value.replaceAllMapped(
      RegExp(r'\d'),
      (match) => '۰۱۲۳۴۵۶۷۸۹'[int.parse(match.group(0)!)],
    );
