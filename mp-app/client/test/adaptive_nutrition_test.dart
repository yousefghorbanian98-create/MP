/// M78 — adaptive TDEE, API deltas, insufficient data and owner-scoped weigh-in.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/nutrition/adaptive_nutrition_card.dart';

class _AdaptiveClient extends http.BaseClient {
  bool fail = false;
  bool enoughData = false;
  bool weightLogged = false;
  Map<String, dynamic>? postedBody;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    dynamic payload;
    var status = 200;
    if (request.method == 'GET' && path == '/nutrition/member/3/adaptive') {
      if (fail) {
        status = 503;
        payload = {'detail': 'گزارش تغذیه در دسترس نیست'};
      } else {
        payload = _report(weightLogged: weightLogged, enoughData: enoughData);
      }
    } else if (request.method == 'POST' && path == '/nutrition/weight-logs') {
      postedBody = jsonDecode((request as http.Request).body) as Map<String, dynamic>;
      weightLogged = true;
      payload = {
        'logged': 1,
        'updated': 0,
        'rejected': [],
        'reason': 'وزن امروز ثبت شد',
        'rule_version': 'adaptive-nutrition-1.0',
      };
    } else {
      status = 404;
      payload = {'detail': 'not found'};
    }
    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      status,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }
}

Map<String, dynamic> _report({required bool weightLogged, bool enoughData = false}) => {
      'member_id': 3,
      'goal': 'weight_loss',
      'current_target_kcal': enoughData ? 2100 : null,
      'plan_id': enoughData ? 8 : null,
      'estimate': {
        'tdee_kcal': enoughData ? 2650.0 : null,
        'confidence': enoughData ? 'medium' : 'insufficient',
        'data_state': enoughData ? 'estimated' : 'insufficient_intake',
        'mean_intake_kcal': enoughData ? 2100.0 : null,
        'reason': enoughData
            ? 'TDEE از روند واقعی وزن و مصرف ثبت‌شده برآورد شده است.'
            : 'فقط ۰ روز غذا ثبت شده؛ دادهٔ کافی برای تخمین وجود ندارد.',
        'trend': {
          'slope_kg_per_week': enoughData ? -0.5 : null,
          'notes': <String>[],
        },
        'assumptions': enoughData ? ['فقط روزهای ثبت‌شده محاسبه شده‌اند'] : <String>[],
      },
      'suggestion': {
        'suggested_target_kcal': enoughData ? 2300 : null,
        'delta_kcal': enoughData ? 200 : 0,
        'action': enoughData ? 'increase' : 'none',
        'reason': enoughData ? 'هدف فعلی با روند نیاز به تعدیل دارد.' : 'TDEE نامعلوم است؛ تغییری پیشنهاد نمی‌شود.',
        'capped': false,
      },
      'data_counts': {
        'weight_entries': weightLogged ? 1 : (enoughData ? 28 : 0),
        'intake_days': enoughData ? 28 : 0,
      },
      'latest_weight_kg': weightLogged ? 74.5 : (enoughData ? 78.0 : null),
      'rule_version': 'adaptive-nutrition-1.0',
    };

Widget _wrap(http.Client client) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith(
          (ref) => AuthController.test(
            AuthState(accessToken: 'test-token', memberId: 3, userName: 'عضو تست'),
          ),
        ),
      ],
      child: MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: ListView(children: [AdaptiveNutritionCard()])),
        ),
      ),
    );

void main() {
  testWidgets('TDEE و delta را از report API نمایش می‌دهد، نه محاسبهٔ Client', (tester) async {
    final client = _AdaptiveClient()..enoughData = true;
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(client.calls, contains('GET /nutrition/member/3/adaptive'));
    expect(find.text('۲۶۵۰ kcal'), findsOneWidget);
    expect(find.text('۲۱۰۰ kcal'), findsWidgets);
    expect(find.textContaining('+۲۰۰ kcal → ۲۳۰۰ kcal'), findsOneWidget);
    expect(find.textContaining('توصیهٔ درمانی یا رژیم پزشکی نیست'), findsOneWidget);
  });

  testWidgets('دادهٔ ناکافی را نامعلوم می‌گوید و با ثبت وزن، API را تازه می‌کند', (tester) async {
    final client = _AdaptiveClient();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('نامعلوم'), findsWidgets);
    expect(find.textContaining('فقط ۰ روز غذا ثبت شده'), findsOneWidget);
    expect(find.text('تغییری پیشنهاد نشده'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('adaptive-weight-field')), '۷۴٫۵');
    await tester.tap(find.byKey(const Key('adaptive-weight-save')));
    await tester.pumpAndSettle();

    expect(client.calls, contains('POST /nutrition/weight-logs'));
    expect(client.calls.where((call) => call == 'GET /nutrition/member/3/adaptive').length,
        greaterThanOrEqualTo(2));
    expect(client.postedBody?['member_id'], 3);
    final entry = (client.postedBody?['entries'] as List).single as Map<String, dynamic>;
    expect(entry['weight_kg'], 74.5);
    expect(entry['logged_for_date'], matches(RegExp(r'^\d{4}-\d{2}-\d{2}$')));
    expect(find.textContaining('۱ ثبت وزن'), findsOneWidget);
    expect(find.text('وزن امروز ثبت شد'), findsOneWidget);
  });

  testWidgets('گزارش API ناموفق empty فرض نمی‌شود و retry دارد', (tester) async {
    final client = _AdaptiveClient()..fail = true;
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('گزارش تغذیه دریافت نشد'), findsOneWidget);
    expect(find.text('تغییری پیشنهاد نشده'), findsNothing);

    client.fail = false;
    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();
    expect(find.text('تغییری پیشنهاد نشده'), findsOneWidget);
    expect(client.calls.where((call) => call == 'GET /nutrition/member/3/adaptive').length,
        greaterThanOrEqualTo(2));
  });

  test('وزن ورودی فارسی/عربی را می‌پذیرد و خارج از قرارداد را رد می‌کند', () {
    expect(parseBodyWeightKg('۷۴٫۵'), 74.5);
    expect(parseBodyWeightKg('٧٤.٥'), 74.5);
    expect(parseBodyWeightKg('19.9'), isNull);
    expect(parseBodyWeightKg('401'), isNull);
    expect(parseBodyWeightKg('نامعلوم'), isNull);
  });
}
