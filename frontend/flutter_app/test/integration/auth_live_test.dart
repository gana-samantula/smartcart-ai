// Runs the real Dio client, interceptor and repository against a running API.
//
// Skipped unless the API URL is supplied:
//   flutter test test/integration/auth_live_test.dart \
//     --dart-define=SMARTCART_LIVE_API=http://127.0.0.1:8000
//
// Each run creates a uniquely named account and deletes it at the end. Use a development
// database, not production.
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartcart_app/features/auth/data/auth_api.dart';
import 'package:smartcart_app/features/auth/data/auth_interceptor.dart';
import 'package:smartcart_app/features/auth/data/http_auth_repository.dart';
import 'package:smartcart_app/features/auth/domain/auth_failure.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

import '../support/in_memory_token_store.dart';

const String _liveApi = String.fromEnvironment('SMARTCART_LIVE_API');
const String _password = 'a live test passphrase';

class _Client {
  _Client(String baseUrl) : store = InMemoryTokenStore() {
    dio = Dio(BaseOptions(baseUrl: baseUrl));
    repository = HttpAuthRepository(api: AuthApi(dio), tokens: store);
    dio.interceptors.add(
      AuthInterceptor(
        dio: dio,
        readAccessToken: () async => (await store.read())?.accessToken,
        refreshAccessToken: () => repository.refreshSession(),
      ),
    );
  }

  final InMemoryTokenStore store;
  late final Dio dio;
  late final HttpAuthRepository repository;
}

void main() {
  group(
    'live API',
    skip: _liveApi.isEmpty
        ? 'set --dart-define=SMARTCART_LIVE_API=<url>'
        : false,
    () {
      late _Client client;
      late String email;

      setUp(() {
        client = _Client(_liveApi);
        email =
            'live-test-${DateTime.now().microsecondsSinceEpoch}@example.com';
      });

      test(
        'register, restore, refresh after expiry, sign out, and delete',
        () async {
          final created = await client.repository.register(
            email: email,
            password: _password,
            displayName: 'Live Test',
          );
          expect(created.email, email);
          expect(created.displayName, 'Live Test');

          // Restore from storage: the access token is valid, so no refresh is needed.
          final restored = await client.repository.restoreSession();
          expect(restored?.email, email);

          // Simulate an expired access token. The refresh token is still good.
          final before = (await client.store.read())!;
          await client.store.write(
            SessionTokens(
              accessToken: 'expired-token-value-for-the-live-test',
              refreshToken: before.refreshToken,
            ),
          );
          final afterExpiry = await client.repository.restoreSession();
          expect(
            afterExpiry?.email,
            email,
            reason: 'interceptor should refresh and retry',
          );
          final rotated = (await client.store.read())!;
          expect(rotated.accessToken, isNot(before.accessToken));
          expect(rotated.refreshToken, isNot(before.refreshToken));

          // Sign out clears local tokens, and the old refresh token no longer works.
          await client.repository.signOut();
          expect(await client.store.read(), isNull);
          expect(await client.repository.restoreSession(), isNull);

          // Sign back in, then delete the account so the live database stays clean.
          final signedIn = await client.repository.signIn(
            email: email,
            password: _password,
          );
          expect(signedIn.email, email);
          await client.dio.post<void>(
            '/api/v1/auth/account/delete',
            data: {'password': _password},
          );
          expect(await client.repository.restoreSession(), isNull);
        },
      );

      test('a wrong password surfaces the API error code', () async {
        await client.repository.register(email: email, password: _password);
        final other = _Client(_liveApi);

        await expectLater(
          other.repository.signIn(
            email: email,
            password: 'the wrong passphrase here',
          ),
          throwsA(
            isA<AuthFailure>()
                .having(
                  (failure) => failure.code,
                  'code',
                  'invalid_credentials',
                )
                .having((failure) => failure.statusCode, 'status', 401),
          ),
        );

        // Clean up through the first client, which still holds valid tokens.
        await client.dio.post<void>(
          '/api/v1/auth/account/delete',
          data: {'password': _password},
        );
      });
    },
  );
}
