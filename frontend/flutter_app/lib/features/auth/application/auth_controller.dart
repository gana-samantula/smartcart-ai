import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smartcart_app/features/auth/application/auth_providers.dart';
import 'package:smartcart_app/features/auth/domain/auth_failure.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

enum AuthStatus { unknown, signedOut, signedIn }

class AuthState {
  const AuthState({required this.status, this.user});

  /// Before the stored session has been checked.
  static const AuthState unknown = AuthState(status: AuthStatus.unknown);

  final AuthStatus status;
  final UserProfile? user;
}

/// Owns the signed-in state that routing depends on.
///
/// Failures from sign-in, registration and password actions are thrown to the caller, so each
/// screen can show them next to its form.
class AuthController extends Notifier<AuthState> {
  @override
  AuthState build() {
    Future<void>.microtask(_restoreSession);
    return AuthState.unknown;
  }

  Future<void> signIn({required String email, required String password}) async {
    final user = await ref
        .read(authRepositoryProvider)
        .signIn(email: email, password: password);
    state = AuthState(status: AuthStatus.signedIn, user: user);
  }

  Future<void> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    final user = await ref
        .read(authRepositoryProvider)
        .register(email: email, password: password, displayName: displayName);
    state = AuthState(status: AuthStatus.signedIn, user: user);
  }

  Future<void> signOut() async {
    await ref.read(authRepositoryProvider).signOut();
    state = const AuthState(status: AuthStatus.signedOut);
  }

  Future<void> _restoreSession() async {
    try {
      final user = await ref.read(authRepositoryProvider).restoreSession();
      state = user == null
          ? const AuthState(status: AuthStatus.signedOut)
          : AuthState(status: AuthStatus.signedIn, user: user);
    } on AuthFailure catch (failure) {
      // Could not reach the server. Show signed out; the tokens are kept for the next launch.
      debugPrint(
        'Session check failed (${failure.code ?? failure.statusCode})',
      );
      state = const AuthState(status: AuthStatus.signedOut);
    }
  }
}

final authControllerProvider = NotifierProvider<AuthController, AuthState>(
  AuthController.new,
);
