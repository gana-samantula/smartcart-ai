import 'package:dio/dio.dart';
import 'package:smartcart_app/features/auth/data/auth_api.dart';

const String _sentTokenKey = 'sentAccessToken';
const String _retriedKey = 'retriedAfterRefresh';

/// Adds the bearer token to API calls, and recovers from an expired access token.
///
/// On a 401, the request is retried once. If the stored token already differs from the one that
/// was sent (another request refreshed first), that token is used. Otherwise the session is
/// refreshed through [refreshAccessToken], which shares a single in-flight rotation.
class AuthInterceptor extends Interceptor {
  AuthInterceptor({
    required this._dio,
    required this._readAccessToken,
    required this._refreshAccessToken,
  });

  final Dio _dio;
  final Future<String?> Function() _readAccessToken;
  final Future<String?> Function() _refreshAccessToken;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    if (options.extra[skipAuthKey] != true) {
      final token = await _readAccessToken();
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
        options.extra[_sentTokenKey] = token;
      }
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final request = err.requestOptions;
    final canRecover =
        err.response?.statusCode == 401 &&
        request.extra[skipAuthKey] != true &&
        request.extra[_retriedKey] != true;
    if (!canRecover) {
      handler.next(err);
      return;
    }

    final token = await _tokenForRetry(request.extra[_sentTokenKey] as String?);
    if (token == null) {
      handler.next(err);
      return;
    }

    request.extra[_retriedKey] = true;
    request.headers['Authorization'] = 'Bearer $token';
    try {
      handler.resolve(await _dio.fetch<dynamic>(request));
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  Future<String?> _tokenForRetry(String? sentToken) async {
    final current = await _readAccessToken();
    if (current != null && current != sentToken) {
      return current;
    }
    return _refreshAccessToken();
  }
}
