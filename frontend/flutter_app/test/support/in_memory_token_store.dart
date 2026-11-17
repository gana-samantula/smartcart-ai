import 'package:smartcart_app/features/auth/data/token_store.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

/// Token storage for tests. Secure storage needs a platform channel, which tests do not have.
class InMemoryTokenStore implements TokenStore {
  SessionTokens? _tokens;

  @override
  Future<SessionTokens?> read() async => _tokens;

  @override
  Future<void> write(SessionTokens tokens) async {
    _tokens = tokens;
  }

  @override
  Future<void> clear() async {
    _tokens = null;
  }
}
