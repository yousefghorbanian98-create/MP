/// چک‌این واقعی — QR امضاشده + چهره (ثبت/چک‌این از API) (M32).
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:qr_flutter/qr_flutter.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import '../../shared/widgets/glass_card.dart';

final qrTokenProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiClientProvider);
  return api.get('/face/qr-token');
});

class CheckInPage extends ConsumerStatefulWidget {
  const CheckInPage({super.key});

  @override
  ConsumerState<CheckInPage> createState() => _CheckInPageState();
}

class _CheckInPageState extends ConsumerState<CheckInPage>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs = TabController(length: 2, vsync: this);
  String? _faceMessage;
  bool _busy = false;

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _faceAction(String endpoint) async {
    setState(() {
      _busy = true;
      _faceMessage = null;
    });
    try {
      final photo = await ImagePicker()
          .pickImage(source: ImageSource.camera, maxWidth: 640);
      if (photo == null) {
        setState(() => _faceMessage = 'عکسی گرفته نشد');
        return;
      }
      final bytes = await photo.readAsBytes();
      final api = ref.read(apiClientProvider);
      final auth = ref.read(authProvider);
      final r = await api.post(endpoint, {
        'member_id': auth.memberId,
        'image_base64': base64Encode(bytes),
      });
      setState(() => _faceMessage = '✅ موفق: ${r['status'] ?? r['result'] ?? 'انجام شد'}');
    } catch (e) {
      setState(() => _faceMessage = '⚠ $e');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final qr = ref.watch(qrTokenProvider);
    return SafeArea(
      child: Column(
        children: [
          TabBar(
            controller: _tabs,
            indicatorColor: MpColors.primary,
            labelColor: MpColors.primary,
            tabs: const [Tab(text: 'QR ورود'), Tab(text: 'چهره')],
          ),
          Expanded(
            child: TabBarView(
              controller: _tabs,
              children: [
                // ── QR ──
                Center(
                  child: qr.when(
                    loading: () => const CircularProgressIndicator(),
                    error: (e, _) => Text('خطا: $e'),
                    data: (t) => GlassCard(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Text('برای ورود نشان دهید',
                              style: TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.bold)),
                          const SizedBox(height: 14),
                          QrImageView(
                            data: t['payload'] as String? ?? '',
                            size: 220,
                            backgroundColor: Colors.white,
                          )
                              .animate()
                              .scale(
                                  begin: const Offset(0.9, 0.9),
                                  duration: 400.ms,
                                  curve: Curves.easeOutBack)
                              .fadeIn(),
                          const SizedBox(height: 12),
                          Text('عضو شمارهٔ ${t['member_id']}',
                              style: TextStyle(color: MpColors.textSecondary)),
                        ],
                      ),
                    ),
                  ),
                ),
                // ── چهره ──
                Center(
                  child: GlassCard(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.face_retouching_natural,
                            size: 56, color: MpColors.primary),
                        const SizedBox(height: 12),
                        const Text('ورود با چهره',
                            style: TextStyle(
                                fontSize: 16, fontWeight: FontWeight.bold)),
                        const SizedBox(height: 6),
                        Text('ابتدا چهره را ثبت کنید، سپس با چک‌این وارد شوید',
                            style: TextStyle(color: MpColors.textSecondary)),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            OutlinedButton.icon(
                              onPressed:
                                  _busy ? null : () => _faceAction('/face/enroll'),
                              icon: const Icon(Icons.app_registration),
                              label: const Text('ثبت چهره'),
                            ),
                            const SizedBox(width: 10),
                            FilledButton.icon(
                              onPressed:
                                  _busy ? null : () => _faceAction('/face/checkin'),
                              icon: const Icon(Icons.login),
                              label: const Text('چک‌این'),
                            ),
                          ],
                        ),
                        if (_busy) ...[
                          const SizedBox(height: 14),
                          const CircularProgressIndicator(),
                        ],
                        if (_faceMessage != null) ...[
                          const SizedBox(height: 12),
                          Text(_faceMessage!,
                              textAlign: TextAlign.center,
                              style: const TextStyle(fontSize: 13)),
                        ],
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
