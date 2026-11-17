/// Member-scoped wallet ledger pages, loaded from persisted credit/debit entries.
library;

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/session.dart';

const _walletPageSize = 20;

final walletLedgerProvider = StateNotifierProvider.autoDispose<WalletLedgerController, WalletLedgerState>(
  (ref) => WalletLedgerController(
    api: ref.watch(apiClientProvider),
    memberId: ref.watch(authProvider).memberId,
  ),
);

class WalletLedgerState {
  const WalletLedgerState({
    this.memberId,
    this.balanceRial,
    this.transactions = const [],
    this.nextBeforeId,
    this.isLoading = false,
    this.isLoadingMore = false,
    this.error,
    this.loadMoreError,
  });

  final int? memberId;
  final int? balanceRial;
  final List<Map<String, dynamic>> transactions;
  final int? nextBeforeId;
  final bool isLoading;
  final bool isLoadingMore;
  final String? error;
  final String? loadMoreError;
}

class WalletLedgerController extends StateNotifier<WalletLedgerState> {
  WalletLedgerController({required this.api, required this.memberId})
      : super(WalletLedgerState(memberId: memberId, isLoading: memberId != null)) {
    if (memberId == null) {
      state = const WalletLedgerState(error: 'شناسهٔ عضو در نشست موجود نیست');
    } else {
      unawaited(loadFirstPage());
    }
  }

  final ApiClient api;
  final int? memberId;

  Future<void> loadFirstPage() async {
    final id = memberId;
    if (id == null) {
      state = const WalletLedgerState(error: 'شناسهٔ عضو در نشست موجود نیست');
      return;
    }
    state = WalletLedgerState(memberId: id, isLoading: true);
    try {
      final page = await _fetchPage(id, null);
      if (!mounted) return;
      state = WalletLedgerState(
        memberId: id,
        balanceRial: page.balanceRial,
        transactions: page.transactions,
        nextBeforeId: page.nextBeforeId,
      );
    } catch (error) {
      if (!mounted) return;
      state = WalletLedgerState(memberId: id, error: error.toString());
    }
  }

  Future<void> loadMore() async {
    final id = memberId;
    final cursor = state.nextBeforeId;
    if (id == null || cursor == null || state.isLoading || state.isLoadingMore) return;

    final previous = state;
    state = WalletLedgerState(
      memberId: id,
      balanceRial: previous.balanceRial,
      transactions: previous.transactions,
      nextBeforeId: cursor,
      isLoadingMore: true,
    );
    try {
      final page = await _fetchPage(id, cursor);
      if (!mounted) return;
      final priorIds = previous.transactions.map((row) => row['id']).toSet();
      final appended = page.transactions.where((row) => !priorIds.contains(row['id'])).toList();
      if (appended.isNotEmpty && previous.transactions.isNotEmpty) {
        final oldestLoaded = previous.transactions.last['id'] as int;
        if ((appended.first['id'] as int) >= oldestLoaded) {
          throw const FormatException('ترتیب صفحه‌های دفتر کیف‌پول معتبر نیست');
        }
      }
      state = WalletLedgerState(
        memberId: id,
        balanceRial: page.balanceRial,
        transactions: [...previous.transactions, ...appended],
        nextBeforeId: page.nextBeforeId,
      );
    } catch (error) {
      if (!mounted) return;
      state = WalletLedgerState(
        memberId: id,
        balanceRial: previous.balanceRial,
        transactions: previous.transactions,
        nextBeforeId: cursor,
        loadMoreError: error.toString(),
      );
    }
  }

  Future<_WalletPage> _fetchPage(int memberId, int? beforeId) async {
    final cursor = beforeId == null ? '' : '&before_id=$beforeId';
    final response = await api.get(
      '/payments/wallet/$memberId/transactions?limit=$_walletPageSize$cursor',
    );
    if (response is! Map) {
      throw const FormatException('پاسخ دفتر کیف‌پول باید یک شیء باشد');
    }
    final data = Map<String, dynamic>.from(response);
    if (data['member_id'] != memberId) {
      throw const FormatException('دفتر کیف‌پول متعلق به عضو نشست نیست');
    }
    final balance = data['balance_rial'];
    if (balance is! int) {
      throw const FormatException('ماندهٔ دفتر کیف‌پول نامعتبر است');
    }
    final rawRows = data['transactions'];
    if (rawRows is! List) {
      throw const FormatException('تراکنش‌های کیف‌پول باید یک فهرست باشند');
    }

    final rows = <Map<String, dynamic>>[];
    var priorId = 0x7fffffffffffffff;
    for (final raw in rawRows) {
      if (raw is! Map) throw const FormatException('رکورد دفتر کیف‌پول نامعتبر است');
      final row = Map<String, dynamic>.from(raw);
      final id = row['id'];
      final amount = row['amount_rial'];
      final createdAt = row['created_at'];
      if (row['member_id'] != memberId ||
          id is! int ||
          id < 1 ||
          id >= priorId ||
          (beforeId != null && id >= beforeId) ||
          amount is! int ||
          amount <= 0 ||
          !const {'credit', 'debit'}.contains(row['kind']) ||
          row['description'] is! String ||
          createdAt is! String ||
          DateTime.tryParse(createdAt) == null) {
        throw const FormatException('رکورد یا ترتیب دفتر کیف‌پول با قرارداد سرور سازگار نیست');
      }
      rows.add(row);
      priorId = id;
    }

    final rawCursor = data['next_before_id'];
    if (rawCursor != null && (rawCursor is! int || rawCursor < 1)) {
      throw const FormatException('نشانگر صفحه‌بندی دفتر کیف‌پول نامعتبر است');
    }
    if (rawCursor != null && (rows.isEmpty || rawCursor != rows.last['id'])) {
      throw const FormatException('نشانگر صفحه‌بندی با آخرین رکورد دفتر هم‌خوان نیست');
    }
    if (rawCursor != null && beforeId != null && rawCursor >= beforeId) {
      throw const FormatException('نشانگر صفحه‌بندی دفتر کیف‌پول پیشرفتی ندارد');
    }
    return _WalletPage(
      balanceRial: balance,
      transactions: rows,
      nextBeforeId: rawCursor as int?,
    );
  }
}

class _WalletPage {
  const _WalletPage({
    required this.balanceRial,
    required this.transactions,
    required this.nextBeforeId,
  });

  final int balanceRial;
  final List<Map<String, dynamic>> transactions;
  final int? nextBeforeId;
}
