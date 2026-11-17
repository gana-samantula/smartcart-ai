import 'package:dio/dio.dart';
import 'package:smartcart_app/features/auth/domain/auth_failure.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

/// Extra request key marking calls that must not carry an access token.
const String skipAuthKey = 'skipAuth';

/// Thin wrapper over the `/api/v1/auth` and `/api/v1/users` endpoints.
///
/// Every Dio error becomes an [AuthFailure] here, so callers never see raw HTTP exceptions.
class AuthApi {
  AuthApi(this._dio);

  final Dio _dio;

  static final Options _publicOptions = Options(extra: {skipAuthKey: true});

  Future<SessionTokens> login({
    required String email,
    required String password,
  }) async {
    final response = await _send(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/login',
        data: {'email': email, 'password': password},
        options: _publicOptions,
      ),
    );
    return SessionTokens.fromJson(_body(response));
  }

  Future<SessionTokens> register({
    required String email,
    required String password,
    String? displayName,
  }) async {
    final response = await _send(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/register',
        data: {
          'email': email,
          'password': password,
          if (displayName != null && displayName.isNotEmpty)
            'display_name': displayName,
        },
        options: _publicOptions,
      ),
    );
    return SessionTokens.fromJson(_body(response));
  }

  Future<SessionTokens> refresh({required String refreshToken}) async {
    final response = await _send(
      () => _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
        options: _publicOptions,
      ),
    );
    return SessionTokens.fromJson(_body(response));
  }

  /// Carries the access token. The interceptor handles 401 by refreshing once.
  Future<void> logout() async {
    await _send(() => _dio.post<void>('/api/v1/auth/logout'));
  }

  Future<void> requestPasswordReset({required String email}) async {
    await _send(
      () => _dio.post<void>(
        '/api/v1/auth/password-reset/request',
        data: {'email': email},
        options: _publicOptions,
      ),
    );
  }

  Future<void> confirmPasswordReset({
    required String token,
    required String newPassword,
  }) async {
    await _send(
      () => _dio.post<void>(
        '/api/v1/auth/password-reset/confirm',
        data: {'token': token, 'new_password': newPassword},
        options: _publicOptions,
      ),
    );
  }

  Future<UserProfile> me() async {
    final response = await _send(
      () => _dio.get<Map<String, dynamic>>('/api/v1/users/me'),
    );
    return UserProfile.fromJson(_body(response));
  }

  Future<Response<T>> _send<T>(Future<Response<T>> Function() call) async {
    try {
      return await call();
    } on DioException catch (error) {
      throw AuthFailure.fromDio(error);
    }
  }

  Map<String, dynamic> _body(Response<Map<String, dynamic>> response) {
    final data = response.data;
    if (data == null) {
      throw const AuthFailure(
        message: 'SmartCart sent an unexpected response.',
      );
    }
    return data;
  }
}
