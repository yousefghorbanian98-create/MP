/// M81 — چت عضو از نشست جاری؛ فهرست، خواندن، ارسال، خطا و مالکیت.
library;

import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:mp_client/core/router.dart';
import 'package:mp_client/core/session.dart';
import 'package:mp_client/core/theme.dart';
import 'package:mp_client/features/chat/member_chat_page.dart';

class _MemberChatClient extends http.BaseClient {
  int conversationListFailures;
  int messageListFailures;
  bool failSend;
  bool failRead;

  _MemberChatClient({
    this.conversationListFailures = 0,
    this.messageListFailures = 0,
    this.failSend = false,
    this.failRead = false,
  });

  final conversations = <Map<String, dynamic>>[_conversation()];
  final messages = <int, List<Map<String, dynamic>>>{41: [_coachMessage()]};
  final calls = <String>[];
  final queryParameters = <Map<String, String>>[];
  final requestBodies = <Map<String, dynamic>>[];
  final sentBodies = <String>[];
  int _nextMessageId = 60;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path.replaceFirst('/api/v1', '');
    calls.add('${request.method} $path');
    queryParameters.add(Map<String, String>.from(request.url.queryParameters));
    dynamic payload;
    var status = 200;

    if (request.method == 'GET' && path == '/chat/conversations') {
      if (conversationListFailures > 0) {
        conversationListFailures--;
        status = 503;
        payload = _error('خطای دریافت فهرست');
      } else {
        payload = conversations;
      }
    } else if (request.method == 'GET' && path == '/members/3/memberships') {
      payload = <dynamic>[];
    } else if (request.method == 'GET' && path == '/notifications/member/3') {
      payload = <dynamic>[];
    } else {
      final messagePath = RegExp(r'^/chat/conversations/(\d+)/messages$').firstMatch(path);
      final readPath = RegExp(r'^/chat/conversations/(\d+)/read$').firstMatch(path);
      if (request.method == 'GET' && messagePath != null) {
        final conversationId = int.parse(messagePath.group(1)!);
        if (messageListFailures > 0) {
          messageListFailures--;
          status = 503;
          payload = _error('خطای دریافت پیام‌ها');
        } else {
          final rows = messages[conversationId] ?? <Map<String, dynamic>>[];
          payload = {
            'conversation_id': conversationId,
            'messages': rows,
            'unread_count': rows
                .where((row) => row['read_at'] == null && row['sender_id'] != 4)
                .length,
            'rule_version': 'chat-1.0',
          };
        }
      } else if (request.method == 'POST' && messagePath != null) {
        final body = _decodeRequestBody(request);
        requestBodies.add(body);
        if (failSend) {
          status = 503;
          payload = _error('ارسال آزمایشی ناموفق');
        } else {
          final conversationId = int.parse(messagePath.group(1)!);
          final text = body['body'];
          if (text is! String) {
            status = 422;
            payload = _error('بدنهٔ نامعتبر');
          } else {
            sentBodies.add(text);
            payload = {
              'id': _nextMessageId++,
              'conversation_id': conversationId,
              'sender_id': 4,
              'sender_role': 'member',
              'body': text,
              'is_system': false,
              'read_at': null,
              'created_at': '2026-11-16T12:15:00Z',
            };
            messages.putIfAbsent(conversationId, () => []).add(payload);
          }
        }
      } else if (request.method == 'POST' && readPath != null) {
        final body = _decodeRequestBody(request);
        requestBodies.add(body);
        if (failRead) {
          status = 403;
          payload = _error('ثبت خوانده‌شدن مجاز نیست');
        } else {
          final conversationId = int.parse(readPath.group(1)!);
          var marked = 0;
          for (final row in messages[conversationId] ?? <Map<String, dynamic>>[]) {
            if (row['sender_id'] != 4 && row['read_at'] == null) {
              row['read_at'] = '2026-11-16T12:20:00Z';
              marked++;
            }
          }
          payload = {'marked_read': marked, 'rule_version': 'chat-1.0'};
        }
      } else {
        status = 404;
        payload = _error('مسیر آزمایشی ناشناخته است');
      }
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

  static Map<String, dynamic> _decodeRequestBody(http.BaseRequest request) {
    if (request is! http.Request || request.body.isEmpty) return <String, dynamic>{};
    final decoded = jsonDecode(request.body);
    return decoded is Map ? Map<String, dynamic>.from(decoded) : <String, dynamic>{};
  }
}

Map<String, dynamic> _conversation({int memberId = 3, String status = 'open'}) => {
      'id': 41,
      'member_id': memberId,
      'coach_id': 9,
      'subject': 'برنامهٔ هفتگی',
      'status': status,
      'last_message_at': '2026-11-16T10:30:00Z',
      'created_at': '2026-11-15T12:00:00Z',
    };

Map<String, dynamic> _coachMessage({String? readAt}) => {
      'id': 51,
      'conversation_id': 41,
      'sender_id': 9,
      'sender_role': 'coach',
      'body': 'برای تمرین امروز وزنه را سبک‌تر انتخاب کن.',
      'is_system': false,
      'read_at': readAt,
      'created_at': '2026-11-16T10:30:00Z',
    };

Map<String, dynamic> _error(String message) => {
      'error': {'code': 'test_error', 'message': message},
    };

Widget _withProviders(_MemberChatClient client, Widget child) => ProviderScope(
      overrides: [
        httpClientProvider.overrideWithValue(client),
        authProvider.overrideWith(
          (ref) => AuthController.test(
            AuthState(
              accessToken: 'member-token',
              userId: 4,
              memberId: 3,
              userName: 'عضو تست',
            ),
          ),
        ),
      ],
      child: child,
    );

Widget _wrap(_MemberChatClient client) => _withProviders(
      client,
      MaterialApp(
        theme: mpTheme(),
        home: const Directionality(
          textDirection: TextDirection.rtl,
          child: MemberChatPage(),
        ),
      ),
    );

Widget _wrapWithRouter(_MemberChatClient client) => _withProviders(
      client,
      MaterialApp.router(
        theme: mpTheme(),
        routerConfig: createMpRouter(initialLocation: '/home'),
        builder: (context, child) => Directionality(
          textDirection: TextDirection.rtl,
          child: child!,
        ),
      ),
    );

void main() {
  testWidgets('فهرست را از endpoint عضو می‌خواند، بدون شناسهٔ قابل‌انتخاب',
      (tester) async {
    final client = _MemberChatClient();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(client.calls, contains('GET /chat/conversations'));
    expect(client.queryParameters.first, isEmpty,
        reason: 'member_id از کلاینت یا query فرستاده نمی‌شود');
    expect(client.calls.any((call) => call.contains('member_id=')), isFalse);
    expect(find.text('برنامهٔ هفتگی'), findsOneWidget);
    expect(find.textContaining('آخرین پیام'), findsOneWidget);
  });

  testWidgets('پیام مربی را می‌خواند و mark-read را به API می‌فرستد',
      (tester) async {
    final client = _MemberChatClient();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();
    await tester.tap(find.text('برنامهٔ هفتگی'));
    await tester.pumpAndSettle();

    expect(client.calls, contains('GET /chat/conversations/41/messages'));
    expect(find.text('برای تمرین امروز وزنه را سبک‌تر انتخاب کن.'), findsOneWidget);
    expect(find.text('۱ پیام خوانده‌نشده · علامت‌گذاری'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('member-chat-mark-read')));
    await tester.pumpAndSettle();

    expect(client.calls, contains('POST /chat/conversations/41/read'));
    expect(client.requestBodies.last, isEmpty);
    expect(find.text('۱ پیام خوانده شد'), findsOneWidget);
    expect(find.text('۱ پیام خوانده‌نشده · علامت‌گذاری'), findsNothing);
    expect(find.textContaining('خوانده‌شده'), findsOneWidget);
  });

  testWidgets('در خطای ارسال متن حفظ می‌شود و پس از موفقیت پاک می‌شود',
      (tester) async {
    final client = _MemberChatClient(failSend: true);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();
    await tester.tap(find.text('برنامهٔ هفتگی'));
    await tester.pumpAndSettle();

    final composer = find.byKey(const ValueKey('member-chat-composer'));
    await tester.enterText(composer, 'سؤال دربارهٔ برنامه');
    await tester.pump();
    await tester.tap(find.byTooltip('ارسال پیام'));
    await tester.pumpAndSettle();

    expect(client.requestBodies.single, {'body': 'سؤال دربارهٔ برنامه'});
    expect(tester.widget<TextField>(composer).controller!.text, 'سؤال دربارهٔ برنامه');
    expect(find.textContaining('ارسال پیام ناموفق بود'), findsOneWidget);

    client.failSend = false;
    await tester.tap(find.byTooltip('ارسال پیام'));
    await tester.pumpAndSettle();

    expect(client.sentBodies, ['سؤال دربارهٔ برنامه']);
    expect(client.requestBodies.last, {'body': 'سؤال دربارهٔ برنامه'});
    expect(tester.widget<TextField>(composer).controller!.text, isEmpty);
    expect(find.text('پیام ارسال شد'), findsOneWidget);
    expect(find.text('سؤال دربارهٔ برنامه'), findsOneWidget);
  });

  testWidgets('فهرست خالی صادقانه است و گفتگوی اشتباه نمی‌سازد',
      (tester) async {
    final client = _MemberChatClient()..conversations.clear();
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.text('هنوز گفتگویی ندارید'), findsOneWidget);
    expect(find.textContaining('از مربی خود بخواهید'), findsOneWidget);
    expect(client.calls.where((call) => call == 'POST /chat/conversations'), isEmpty);
  });

  testWidgets('خطای فهرست empty جا زده نمی‌شود و retry دارد', (tester) async {
    final client = _MemberChatClient(conversationListFailures: 1);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('دریافت گفتگوها ناموفق بود'), findsOneWidget);
    expect(find.text('هنوز گفتگویی ندارید'), findsNothing);

    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();

    expect(client.calls.where((call) => call == 'GET /chat/conversations').length, 2);
    expect(find.text('برنامهٔ هفتگی'), findsOneWidget);
  });

  testWidgets('خطای خواندن پیام‌ها retry می‌شود و به گفتگوی خالی تبدیل نمی‌شود',
      (tester) async {
    final client = _MemberChatClient(messageListFailures: 1);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();
    await tester.tap(find.text('برنامهٔ هفتگی'));
    await tester.pumpAndSettle();

    expect(find.textContaining('دریافت پیام‌ها ناموفق بود'), findsOneWidget);
    expect(find.text('هنوز پیامی در این گفتگو نیست. پیام خود را بنویسید.'), findsNothing);

    await tester.tap(find.text('تلاش دوباره'));
    await tester.pumpAndSettle();

    expect(client.calls.where((call) => call == 'GET /chat/conversations/41/messages').length,
        2);
    expect(find.text('برای تمرین امروز وزنه را سبک‌تر انتخاب کن.'), findsOneWidget);
  });

  testWidgets('پاسخ خارج از مالکیت نشست رد می‌شود', (tester) async {
    final client = _MemberChatClient();
    client.conversations[0] = _conversation(memberId: 99);
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();

    expect(find.textContaining('گفتگوی دریافتی به عضو جاری تعلق ندارد'), findsOneWidget);
    expect(find.text('برنامهٔ هفتگی'), findsNothing);
    expect(client.calls.any((call) => call.contains('member_id=')), isFalse);
  });

  testWidgets('گفتگوی بسته پیام تازه نمی‌پذیرد', (tester) async {
    final client = _MemberChatClient();
    client.conversations[0] = _conversation(status: 'closed');
    await tester.pumpWidget(_wrap(client));
    await tester.pumpAndSettle();
    await tester.tap(find.text('برنامهٔ هفتگی'));
    await tester.pumpAndSettle();

    expect(find.text('این گفتگو بسته شده است و پیام تازه نمی‌پذیرد.'), findsOneWidget);
    expect(find.byKey(const ValueKey('member-chat-composer')), findsNothing);
  });

  testWidgets('ورودی گفتگو از گرید خانه به صفحهٔ چت واقعی می‌رسد',
      (tester) async {
    final client = _MemberChatClient();
    await tester.pumpWidget(_wrapWithRouter(client));
    await tester.pumpAndSettle();

    final entry = find.text('گفتگو با مربی').first;
    await tester.ensureVisible(entry);
    await tester.tap(entry);
    await tester.pumpAndSettle();

    expect(client.calls, contains('GET /chat/conversations'));
    expect(find.text('برنامهٔ هفتگی'), findsOneWidget);
  });
}
