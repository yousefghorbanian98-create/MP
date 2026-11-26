import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mp_client/features/checkin/checkin_page.dart';
import 'package:qr_flutter/qr_flutter.dart';

Widget _page(Future<bool> Function() auth, void Function() onFetch) {
  return ProviderScope(
    overrides: [
      qrBiometricProvider.overrideWithValue(auth),
      qrTokenProvider.overrideWith((ref) async {
        onFetch();
        return {'payload': 'test-qr', 'member_id': 3};
      }),
      faceConsentProvider.overrideWith((ref) async => {'consent': false}),
    ],
    child: const MaterialApp(home: Scaffold(body: CheckInPage())),
  );
}

void main() {
  testWidgets(
      'QR is fetched only after biometric success and hidden after 30 seconds',
      (tester) async {
    var fetched = 0;
    await tester.pumpWidget(_page(() async => true, () => fetched++));
    await tester.pump();
    expect(find.byType(QrImageView), findsNothing);
    expect(fetched, 0);
    await tester.tap(find.text('نمایش QR'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.byType(QrImageView), findsOneWidget);
    expect(find.text('QR یک‌بارمصرف برای پذیرش'), findsOneWidget);
    expect(
        find.text('نمایش QR به‌تنهایی حضور را ثبت نمی‌کند.'), findsOneWidget);
    expect(find.text('برای ورود نشان دهید'), findsNothing);
    expect(fetched, 1);
    await tester.pump(const Duration(seconds: 30));
    expect(find.byType(QrImageView), findsNothing);
  });

  testWidgets('failed biometric never fetches or displays QR', (tester) async {
    var fetched = 0;
    await tester.pumpWidget(_page(() async => false, () => fetched++));
    await tester.pump();
    await tester.tap(find.text('نمایش QR'));
    await tester.pump();
    expect(find.byType(QrImageView), findsNothing);
    expect(fetched, 0);
    expect(find.text('احراز هویت بیومتریک تأیید نشد.'), findsOneWidget);
  });

  testWidgets('backgrounding the app hides the QR', (tester) async {
    await tester.pumpWidget(_page(() async => true, () {}));
    await tester.pump();
    await tester.tap(find.text('نمایش QR'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.byType(QrImageView), findsOneWidget);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
    tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
    await tester.pump();
    expect(find.byType(QrImageView), findsNothing);
    await tester.pump(const Duration(seconds: 1));
  });
}
