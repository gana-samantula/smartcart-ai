import 'package:flutter/foundation.dart';
import 'package:smartcart_app/features/auth/data/auth_api.dart';
import 'package:smartcart_app/features/auth/data/session_refresher.dart';
import 'package:smartcart_app/features/auth/data/token_store.dart';
import 'package:smartcart_app/features/auth/domain/auth_failure.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';
import 'package:smartcart_app/features/auth/domain/auth_repository.dart';

class HttpAuthRepository implements AuthRepository {
  HttpAuthRepository({required this._api, required this._tokens}) {
    _refresher = SessionRefresher(_rotateTokens);
  }

  final AuthApi _api;
  final TokenStore _tokens;
  late final SessionRefresher _refresher;

  @override
  Future<UserProfile?> restoreSession() async {
    final stored = await _tokens.read();
    if (stored == null) {
      return null;
    }
    try {
      return await _api.me();
    } on AuthFailure catch (failure) {
      if (failure.isUnauthorized) {
        await _tokens.clear();
        return null;
      }
      // Offline or server error: keep the tokens so the next launch can try again.
      rethrow;
    }
  }

  @override
  Future<UserProfile> signIn({
    required String email,
    required String password,
  }) async {
    final tokens = await _api.login(email: email, password: password);
    return _establish(tokens);
  }

  @override
  Future<UserProfile> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    final tokens = await _api.register(
      email: email,
      password: password,
      displayName: displayName,
    );
    return _establish(tokens);
  }

  @override
  Future<void> signOut() async {
    final stored = await _tokens.read();
    if (stored != null) {
      try {
        await _api.logout();
      } on AuthFailure catch (failure) {
        // The server session may stay open until it expires. Local tokens are cleared regardless.
        debugPrint(
          'Server sign-out failed (${failure.code ?? failure.statusCode})',
        );
      }
    }
    await _tokens.clear();
  }

  @override
  Future<void> requestPasswordReset({required String email}) {
    return _api.requestPasswordReset(email: email);
  }

  @override
  Future<void> confirmPasswordReset({
    required String token,
    required String newPassword,
  }) {
    return _api.confirmPasswordReset(token: token, newPassword: newPassword);
  }

  @override
  Future<String?> refreshSession() => _refresher.refresh();

  Future<UserProfile> _establish(SessionTokens tokens) async {
    await _tokens.write(tokens);
    try {
      return await _api.me();
    } on AuthFailure {
      await _tokens.clear();
      rethrow;
    }
  }

  Future<String?> _rotateTokens() async {
    final stored = await _tokens.read();
    if (stored == null) {
      return null;
    }
    try {
      final rotated = await _api.refresh(refreshToken: stored.refreshToken);
      await _tokens.write(rotated);
      return rotated.accessToken;
    } on AuthFailure catch (failure) {
      if (failure.isUnauthorized) {
        // The server has ended this session. Local tokens can never work again.
        await _tokens.clear();
      }
      return null;
    }
  }
}
