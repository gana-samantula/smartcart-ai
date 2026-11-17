import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

/// Where session tokens live between launches.
abstract class TokenStore {
  Future<SessionTokens?> read();

  Future<void> write(SessionTokens tokens);

  Future<void> clear();
}

/// Tokens in the iOS Keychain and Android Keystore-backed storage.
///
/// Platform errors propagate. They are not swallowed, because a silent failure here would look
/// like a signed-out user.
class SecureTokenStore implements TokenStore {
  SecureTokenStore([FlutterSecureStorage? storage])
    : _storage = storage ?? const FlutterSecureStorage();

  static const _accessKey = 'smartcart.access_token';
  static const _refreshKey = 'smartcart.refresh_token';

  final FlutterSecureStorage _storage;

  @override
  Future<SessionTokens?> read() async {
    final access = await _storage.read(key: _accessKey);
    final refresh = await _storage.read(key: _refreshKey);
    if (access == null || refresh == null) {
      return null;
    }
    return SessionTokens(accessToken: access, refreshToken: refresh);
  }

  @override
  Future<void> write(SessionTokens tokens) async {
    await _storage.write(key: _accessKey, value: tokens.accessToken);
    await _storage.write(key: _refreshKey, value: tokens.refreshToken);
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }
}
