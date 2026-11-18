/// تغییر امن شمارهٔ ورود با تأیید جداگانهٔ شمارهٔ فعلی و شمارهٔ جدید.
library;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/session.dart';

class PhoneChangeDialog extends ConsumerStatefulWidget {
  const PhoneChangeDialog({super.key, required this.currentPhone});

  final String currentPhone;

  @override
  ConsumerState<PhoneChangeDialog> createState() => _PhoneChangeDialogState();
}

enum _PhoneChangeStep { request, verifyCurrent, verifyNew }

class _PhoneChangeDialogState extends ConsumerState<PhoneChangeDialog> {
  final _phone = TextEditingController();
  final _code = TextEditingController();
  _PhoneChangeStep _step = _PhoneChangeStep.request;
  String? _challengeId;
  String? _devCode;
  String? _error;
  bool _busy = false;

  @override
  void dispose() {
    _phone.dispose();
    _code.dispose();
    super.dispose();
  }

  String _asciiDigits(String value) => String.fromCharCodes(
        value.runes.map((rune) {
          if (rune >= 0x06f0 && rune <= 0x06f9) return rune - 0x06f0 + 0x30;
          if (rune >= 0x0660 && rune <= 0x0669) return rune - 0x0660 + 0x30;
          return rune;
        }),
      );

  Future<void> _submit() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      if (_step == _PhoneChangeStep.request) {
        final phone = _asciiDigits(_phone.text.trim());
        if (!RegExp(r'^09\d{9}$').hasMatch(phone)) {
          throw ApiException('شمارهٔ موبایل معتبر نیست (مثال: 09121234567)');
        }
        final response = Map<String, dynamic>.from(
          await api.post('/auth/phone-change/request', {'new_phone': phone})
              as Map,
        );
        _challengeId = response['challenge_id'] as String?;
        if (_challengeId == null || _challengeId!.isEmpty) {
          throw ApiException('شناسهٔ درخواست از سرور دریافت نشد');
        }
        _devCode = response['dev_code'] as String?;
        _code.clear();
        setState(() => _step = _PhoneChangeStep.verifyCurrent);
      } else if (_step == _PhoneChangeStep.verifyCurrent) {
        final result = Map<String, dynamic>.from(
          await api.post('/auth/phone-change/verify-old', {
            'challenge_id': _challengeId,
            'code': _asciiDigits(_code.text.trim()),
          }) as Map,
        );
        _devCode = result['dev_code'] as String?;
        _code.clear();
        setState(() => _step = _PhoneChangeStep.verifyNew);
      } else {
        final result = Map<String, dynamic>.from(
          await api.post('/auth/phone-change/confirm', {
            'challenge_id': _challengeId,
            'code': _asciiDigits(_code.text.trim()),
          }) as Map,
        );
        if (result['status'] != 'phone_changed') {
          throw ApiException('تغییر شماره از سوی سرور تأیید نشد');
        }
        if (mounted) Navigator.of(context).pop(true);
      }
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String get _title => switch (_step) {
        _PhoneChangeStep.request => 'تغییر شمارهٔ موبایل',
        _PhoneChangeStep.verifyCurrent => 'تأیید شمارهٔ فعلی',
        _PhoneChangeStep.verifyNew => 'تأیید شمارهٔ جدید',
      };

  String get _buttonLabel => switch (_step) {
        _PhoneChangeStep.request => 'ارسال کد به شمارهٔ فعلی',
        _PhoneChangeStep.verifyCurrent => 'تأیید کد فعلی و ارسال کد جدید',
        _PhoneChangeStep.verifyNew => 'تأیید و تغییر شماره',
      };

  @override
  Widget build(BuildContext context) {
    final askingForPhone = _step == _PhoneChangeStep.request;
    final currentStage = _step == _PhoneChangeStep.verifyCurrent;
    return AlertDialog(
      title: Text(_title),
      content: SizedBox(
        width: 420,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              askingForPhone
                  ? 'برای امنیت، ابتدا کد شمارهٔ فعلی و سپس کد شمارهٔ جدید لازم است. '
                      'اگر به شمارهٔ فعلی دسترسی ندارید، این مسیر بازیابی قابل استفاده نیست.'
                  : currentStage
                      ? 'کد تأیید به شمارهٔ فعلی ${widget.currentPhone} فرستاده شد.'
                      : 'شمارهٔ فعلی تأیید شد؛ کد جداگانه به شمارهٔ جدید فرستاده شد.',
            ),
            const SizedBox(height: 16),
            if (askingForPhone)
              TextField(
                controller: _phone,
                keyboardType: TextInputType.phone,
                maxLength: 11,
                decoration: const InputDecoration(
                  labelText: 'شمارهٔ جدید',
                  hintText: '09xxxxxxxxx',
                  border: OutlineInputBorder(),
                ),
              )
            else
              TextField(
                controller: _code,
                keyboardType: TextInputType.number,
                maxLength: 6,
                autofocus: true,
                decoration: InputDecoration(
                  labelText: currentStage ? 'کد شمارهٔ فعلی' : 'کد شمارهٔ جدید',
                  helperText: _devCode == null ? null : 'کد آزمایشی: $_devCode',
                  border: const OutlineInputBorder(),
                ),
              ),
            if (_error != null) ...[
              const SizedBox(height: 8),
              Text(_error!, style: const TextStyle(color: Colors.redAccent)),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _busy ? null : () => Navigator.of(context).pop(false),
          child: const Text('انصراف'),
        ),
        FilledButton(
          onPressed: _busy ? null : _submit,
          child: Text(_busy ? 'لطفاً صبر کنید…' : _buttonLabel),
        ),
      ],
    );
  }
}
