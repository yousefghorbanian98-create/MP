/// M73 — آزمون مسیر کاربر از کاتالوگ ایرانی تا جمع API روزانه.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/nutrition/nutrition_page.dart';

class _NutritionClient extends http.BaseClient {
  bool logged = false;
  Map<String, dynamic>? postedBody;
  final List<String> calls = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    dynamic payload;

    if (request.method == 'GET' && path == '/nutrition/plans/member/3') {
      payload = [];
    } else if (request.method == 'GET' &&
        path == '/nutrition/member/3/adaptive') {
      payload = {
        'member_id': 3,
        'goal': 'fitness',
        'current_target_kcal': null,
        'plan_id': null,
        'estimate': {
          'tdee_kcal': null,
          'confidence': 'insufficient',
          'data_state': 'insufficient_intake',
          'mean_intake_kcal': null,
          'reason': 'برای تخمین دادهٔ کافی نیست',
          'trend': {'slope_kg_per_week': null, 'notes': []},
        },
        'suggestion': {
          'suggested_target_kcal': null,
          'delta_kcal': 0,
          'action': 'none',
          'reason': 'دادهٔ کافی نیست',
        },
        'data_counts': {'weight_entries': 0, 'intake_days': 0},
        'latest_weight_kg': null,
      };
    } else if (request.method == 'POST' && path == '/nutrition/weight-logs') {
      payload = {
        'logged': 1,
        'updated': 0,
        'rejected': [],
        'reason': 'وزن ثبت شد',
      };
    } else if (request.method == 'GET' && path == '/nutrition/foods') {
      final query = request.url.queryParameters['q'] ?? '';
      payload = query.contains('قورمه') ? [_ghormehFood] : [];
    } else if (request.method == 'GET' &&
        path == '/nutrition/food-logs/member/3/daily') {
      final date = request.url.queryParameters['date'];
      payload = logged
          ? {
              'member_id': 3,
              'date': date,
              'items': [
                {
                  'id': 10,
                  'food_id': 7,
                  'name_fa': 'قورمه سبزی',
                  'grams': 150.0,
                  'meal_slot': 'snack',
                  'kcal': 270.0,
                  'protein_g': 18.0,
                  'carbs_g': 12.0,
                  'fat_g': 16.6,
                  'warning': '',
                },
              ],
              'totals': {
                'kcal': 270.0,
                'protein_g': 18.0,
                'carbs_g': 12.0,
                'fat_g': 16.6,
              },
              'data_state': 'logged',
              'target_source': 'none',
            }
          : {
              'member_id': 3,
              'date': date,
              'items': [],
              'totals': {
                'kcal': 0.0,
                'protein_g': 0.0,
                'carbs_g': 0.0,
                'fat_g': 0.0,
              },
              'data_state': 'nothing_logged',
              'target_source': 'none',
              'reason': 'برای امروز چیزی ثبت نشده است',
            };
    } else if (request.method == 'POST' && path == '/nutrition/food-logs') {
      postedBody =
          jsonDecode((request as http.Request).body) as Map<String, dynamic>;
      logged = true;
      payload = {
        'logged': 1,
        'rejected': [],
        'reason': '۱ وعده ثبت شد',
        'rule_version': 'food-logging-1.0',
      };
    } else {
      payload = <String, dynamic>{};
    }

    final bytes = utf8.encode(jsonEncode(payload));
    return http.StreamedResponse(
      Stream.value(bytes),
      200,
      contentLength: bytes.length,
      headers: {'content-type': 'application/json'},
      request: request,
    );
  }

  static const _ghormehFood = {
    'id': 7,
    'name_fa': 'قورمه سبزی',
    'category': 'غذای ایرانی',
    'kcal_per_100g': 180,
    'protein_g_per_100g': 12.0,
    'carbs_g_per_100g': 8.0,
    'fat_g_per_100g': 11.1,
    'dry_or_raw': false,
  };
}

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
      child: Scaffold(body: NutritionPage()),
    ),
  ),
);

void main() {
  testWidgets(
    'غذای ایرانی را با گرم فارسی ثبت می‌کند و جمع واقعی را تازه می‌کند',
    (tester) async {
      final client = _NutritionClient();
      await tester.pumpWidget(_wrap(client));
      await tester.pumpAndSettle();

      expect(find.text('ثبت غذای امروز'), findsOneWidget);
      expect(find.textContaining('Food Finder (MIT)'), findsOneWidget);
      expect(
        find.textContaining('مصرف امروز هنوز ثبت نشده است'),
        findsOneWidget,
      );
      expect(
        find.textContaining('۰ کیلوکالری'),
        findsNothing,
        reason: 'nothing_logged نباید به مصرف واقعی صفر تعبیر شود',
      );

      await tester.ensureVisible(find.byKey(const Key('food-search-field')));
      await tester.enterText(
        find.byKey(const Key('food-search-field')),
        'قورمه سبزی',
      );
      await tester.ensureVisible(find.byTooltip('جست‌وجو'));
      await tester.tap(find.byTooltip('جست‌وجو'));
      await tester.pumpAndSettle();
      expect(find.text('قورمه سبزی'), findsWidgets);
      expect(find.textContaining('غذای ایرانی'), findsOneWidget);

      await tester.ensureVisible(find.text('انتخاب'));
      await tester.tap(find.text('انتخاب'));
      await tester.pumpAndSettle();
      await tester.ensureVisible(find.byKey(const Key('food-grams-field')));
      await tester.enterText(find.byKey(const Key('food-grams-field')), '۱۵۰');
      await tester.ensureVisible(find.byKey(const Key('food-log-save')));
      await tester.tap(find.byKey(const Key('food-log-save')));
      await tester.pumpAndSettle();

      expect(
        client.calls.any((call) => call == 'GET /nutrition/foods'),
        isTrue,
      );
      expect(
        client.calls.any((call) => call == 'POST /nutrition/food-logs'),
        isTrue,
      );
      final body = client.postedBody!;
      expect(body['member_id'], 3);
      final entry = (body['entries'] as List).single as Map<String, dynamic>;
      expect(entry['food_id'], 7);
      expect(
        entry['grams'],
        150.0,
        reason: 'رقم فارسی باید به مقدار API تبدیل شود',
      );
      expect(entry['meal_slot'], 'snack');
      expect(entry['logged_for_date'], matches(RegExp(r'^\d{4}-\d{2}-\d{2}$')));

      expect(find.text('۲۷۰ کیلوکالری'), findsOneWidget);
      expect(find.text('۱۸ گرم پروتئین'), findsOneWidget);
      expect(find.text('۱۲ گرم کربوهیدرات'), findsOneWidget);
      expect(
        find.textContaining('چربی به‌دلیل نبود مقدار مستقیم'),
        findsNothing,
      );
      expect(find.textContaining('چربی در منبع مستقیم نیست'), findsOneWidget);
    },
  );

  test(
    'تجزیهٔ مقدار گرم، رقم فارسی/عربی را می‌پذیرد و مقدار نامعتبر را رد می‌کند',
    () {
      expect(parseFoodLogGrams('۱۵۰٫۵'), 150.5);
      expect(parseFoodLogGrams('١٢٥'), 125);
      expect(parseFoodLogGrams('0'), isNull);
      expect(parseFoodLogGrams('5001'), isNull);
      expect(parseFoodLogGrams('نامعلوم'), isNull);
    },
  );
}
