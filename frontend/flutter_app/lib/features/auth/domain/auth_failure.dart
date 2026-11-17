import 'package:dio/dio.dart';

/// A sign-in or account action failed. [message] is safe to show to the user.
class AuthFailure implements Exception {
  const AuthFailure({required this.message, this.code, this.statusCode});

  /// Shown when the device could not reach the API at all.
  static const AuthFailure network = AuthFailure(
    message: "Can't reach SmartCart. Check your connection and try again.",
  );

  final String message;

  /// Stable machine-readable code from the API, such as `invalid_credentials`.
  final String? code;

  /// HTTP status from the API. Null when the request never got a response.
  final int? statusCode;

  bool get isUnauthorized => statusCode == 401;

  @override
  String toString() => 'AuthFailure($code, $statusCode): $message';

  /// Maps a Dio error to a failure, reading the API's error envelope when one is present.
  static AuthFailure fromDio(DioException error) {
    final status = error.response?.statusCode;
    if (status == null) {
      return AuthFailure.network;
    }
    final body = error.response?.data;
    String? code;
    String? message;
    if (body is Map && body['error'] is Map) {
      final envelope = body['error'] as Map;
      code = envelope['code'] as String?;
      message = envelope['message'] as String?;
    }
    return AuthFailure(
      message: message ?? 'Something went wrong. Please try again.',
      code: code,
      statusCode: status,
    );
  }
}
