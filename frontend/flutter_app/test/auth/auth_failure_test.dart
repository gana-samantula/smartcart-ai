import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smartcart_app/features/auth/domain/auth_failure.dart';

DioException _dioError({int? status, Object? data}) {
  final options = RequestOptions(path: '/api/v1/auth/login');
  return DioException(
    requestOptions: options,
    response: status == null
        ? null
        : Response<Object?>(
            requestOptions: options,
            statusCode: status,
            data: data,
          ),
  );
}

void main() {
  test('a request that never got a response is a network failure', () {
    final failure = AuthFailure.fromDio(_dioError());
    expect(failure.message, AuthFailure.network.message);
    expect(failure.statusCode, isNull);
  });

  test('the API error envelope supplies code and message', () {
    final failure = AuthFailure.fromDio(
      _dioError(
        status: 401,
        data: {
          'error': {
            'code': 'invalid_credentials',
            'message': 'Email or password is incorrect.',
            'details': <String, dynamic>{},
            'request_id': 'abc',
          },
        },
      ),
    );
    expect(failure.code, 'invalid_credentials');
    expect(failure.message, 'Email or password is incorrect.');
    expect(failure.isUnauthorized, isTrue);
  });

  test('an unexpected body still produces a readable message', () {
    final failure = AuthFailure.fromDio(
      _dioError(status: 502, data: '<html>bad gateway</html>'),
    );
    expect(failure.message, 'Something went wrong. Please try again.');
    expect(failure.statusCode, 502);
    expect(failure.isUnauthorized, isFalse);
  });
}
