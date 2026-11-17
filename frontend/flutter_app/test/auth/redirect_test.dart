import 'package:flutter_test/flutter_test.dart';
import 'package:smartcart_app/app/router.dart';
import 'package:smartcart_app/features/auth/application/auth_controller.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

const _signedIn = AuthState(
  status: AuthStatus.signedIn,
  user: UserProfile(id: 'u', email: 'a@example.com'),
);
const _signedOut = AuthState(status: AuthStatus.signedOut);

void main() {
  test(
    'while the session is unknown, every route waits on the splash screen',
    () {
      expect(redirectFor(AuthState.unknown, '/home'), '/splash');
      expect(redirectFor(AuthState.unknown, '/splash'), isNull);
    },
  );

  test('signed-out users may open public routes only', () {
    expect(redirectFor(_signedOut, '/login'), isNull);
    expect(redirectFor(_signedOut, '/register'), isNull);
    expect(redirectFor(_signedOut, '/reset-password'), isNull);
    expect(redirectFor(_signedOut, '/home'), '/welcome');
    expect(redirectFor(_signedOut, '/receipts'), '/welcome');
  });

  test('signed-in users leave auth screens for home', () {
    expect(redirectFor(_signedIn, '/login'), '/home');
    expect(redirectFor(_signedIn, '/splash'), '/home');
    expect(redirectFor(_signedIn, '/home'), isNull);
    expect(redirectFor(_signedIn, '/lists'), isNull);
  });
}
