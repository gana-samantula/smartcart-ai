import 'package:smartcart_app/features/auth/domain/auth_models.dart';

/// Everything the UI needs from authentication. Screens depend on this interface, not on HTTP.
abstract class AuthRepository {
  /// Returns the stored session's user, or null when there is no usable session.
  Future<UserProfile?> restoreSession();

  Future<UserProfile> signIn({required String email, required String password});

  Future<UserProfile> register({
    required String email,
    required String password,
    String? displayName,
  });

  /// Ends the session on the server when possible, then clears local tokens either way.
  Future<void> signOut();

  /// Always succeeds from the caller's view, because the server does not reveal whether the
  /// email is registered.
  Future<void> requestPasswordReset({required String email});

  Future<void> confirmPasswordReset({
    required String token,
    required String newPassword,
  });

  /// Exchanges the stored refresh token for a new pair. Returns the new access token, or null
  /// when the session has ended.
  Future<String?> refreshSession();
}
