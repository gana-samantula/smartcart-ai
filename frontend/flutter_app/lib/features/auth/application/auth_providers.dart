import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:smartcart_app/core/config/api_config.dart';
import 'package:smartcart_app/features/auth/data/auth_api.dart';
import 'package:smartcart_app/features/auth/data/auth_interceptor.dart';
import 'package:smartcart_app/features/auth/data/http_auth_repository.dart';
import 'package:smartcart_app/features/auth/data/token_store.dart';
import 'package:smartcart_app/features/auth/domain/auth_repository.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) => SecureTokenStore());

final Provider<Dio> dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
      headers: {'Accept': 'application/json'},
    ),
  );
  final tokens = ref.watch(tokenStoreProvider);
  dio.interceptors.add(
    AuthInterceptor(
      dio: dio,
      readAccessToken: () async => (await tokens.read())?.accessToken,
      // Read lazily: the repository depends on this client, so reading it at build time would
      // create a cycle.
      refreshAccessToken: () =>
          ref.read(authRepositoryProvider).refreshSession(),
    ),
  );
  return dio;
});

final Provider<AuthApi> authApiProvider = Provider<AuthApi>(
  (ref) => AuthApi(ref.watch(dioProvider)),
);

final Provider<AuthRepository> authRepositoryProvider =
    Provider<AuthRepository>(
      (ref) => HttpAuthRepository(
        api: ref.watch(authApiProvider),
        tokens: ref.watch(tokenStoreProvider),
      ),
    );
