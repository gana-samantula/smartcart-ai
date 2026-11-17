import 'package:smartcart_app/features/auth/domain/auth_failure.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';
import 'package:smartcart_app/features/auth/domain/auth_repository.dart';

/// In-memory stand-in for the HTTP repository. Passwords and reset codes match the fixed values
/// below, so tests can exercise both success and failure paths without a server.
class FakeAuthRepository implements AuthRepository {
  FakeAuthRepository({this.restored});

  static const String password = 'correct horse battery staple';
  static const String resetCode = 'valid-reset-code-123';

  UserProfile? restored;
  final List<String> resetRequests = [];
  int signOutCalls = 0;

  @override
  Future<UserProfile?> restoreSession() async => restored;

  @override
  Future<UserProfile> signIn({
    required String email,
    required String password,
  }) async {
    if (password != FakeAuthRepository.password) {
      throw const AuthFailure(
        message: 'Email or password is incorrect.',
        code: 'invalid_credentials',
        statusCode: 401,
      );
    }
    return UserProfile(id: 'user-1', email: email);
  }

  @override
  Future<UserProfile> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    return UserProfile(id: 'user-2', email: email, displayName: displayName);
  }

  @override
  Future<void> signOut() async {
    signOutCalls += 1;
    restored = null;
  }

  @override
  Future<void> requestPasswordReset({required String email}) async {
    resetRequests.add(email);
  }

  @override
  Future<void> confirmPasswordReset({
    required String token,
    required String newPassword,
  }) async {
    if (token != resetCode) {
      throw const AuthFailure(
        message: 'This reset link is invalid or has expired.',
        code: 'invalid_reset_token',
        statusCode: 400,
      );
    }
  }

  @override
  Future<String?> refreshSession() async => null;
}
