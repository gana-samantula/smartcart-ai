import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:material_ui/material_ui.dart';
import 'package:smartcart_app/app/app.dart';
import 'package:smartcart_app/features/auth/application/auth_providers.dart';
import 'package:smartcart_app/features/auth/domain/auth_models.dart';

import 'support/fake_auth_repository.dart';

/// The splash screen has an indeterminate spinner, which never settles, so pumpAndSettle would
/// time out. Pump a fixed number of frames instead.
Future<void> _settle(WidgetTester tester) async {
  for (var i = 0; i < 10; i++) {
    await tester.pump(const Duration(milliseconds: 100));
  }
}

Future<void> _pumpApp(
  WidgetTester tester,
  FakeAuthRepository repository,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [authRepositoryProvider.overrideWithValue(repository)],
      child: const SmartCartApp(),
    ),
  );
  await _settle(tester);
}

void main() {
  testWidgets('no stored session: welcome, then sign in, then sign out', (
    tester,
  ) async {
    final repository = FakeAuthRepository();
    await _pumpApp(tester, repository);

    expect(find.text('Create account'), findsOneWidget);
    await tester.tap(find.widgetWithText(OutlinedButton, 'Sign in'));
    await _settle(tester);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'shopper@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Password'),
      FakeAuthRepository.password,
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await _settle(tester);

    expect(find.text('Welcome to SmartCart AI'), findsOneWidget);
    expect(find.text('shopper@example.com'), findsOneWidget);

    await tester.tap(find.byTooltip('Sign out'));
    await _settle(tester);

    expect(repository.signOutCalls, 1);
    expect(find.text('Create account'), findsOneWidget);
  });

  testWidgets('a stored session opens home directly', (tester) async {
    final repository = FakeAuthRepository(
      restored: const UserProfile(id: 'u', email: 'saved@example.com'),
    );
    await _pumpApp(tester, repository);

    expect(find.text('saved@example.com'), findsOneWidget);
    expect(find.text('Create account'), findsNothing);
  });

  testWidgets('a wrong password shows the API message and stays on the form', (
    tester,
  ) async {
    await _pumpApp(tester, FakeAuthRepository());
    await tester.tap(find.widgetWithText(OutlinedButton, 'Sign in'));
    await _settle(tester);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'shopper@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Password'),
      'the wrong password value',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await _settle(tester);

    expect(find.text('Email or password is incorrect.'), findsOneWidget);
    expect(find.text('Welcome back'), findsOneWidget);
  });

  testWidgets('sign-in validates the email before calling the server', (
    tester,
  ) async {
    await _pumpApp(tester, FakeAuthRepository());
    await tester.tap(find.widgetWithText(OutlinedButton, 'Sign in'));
    await _settle(tester);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'not-an-email',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Sign in'));
    await _settle(tester);

    expect(find.text('Enter a valid email address.'), findsOneWidget);
    expect(find.text('Welcome back'), findsOneWidget);
  });

  testWidgets('registration rejects mismatched passwords', (tester) async {
    await _pumpApp(tester, FakeAuthRepository());
    await tester.tap(find.widgetWithText(FilledButton, 'Create account'));
    await _settle(tester);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'new@example.com',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Password'),
      'a long enough passphrase',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Confirm password'),
      'a different passphrase',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Create account'));
    await _settle(tester);

    expect(find.text('Passwords do not match.'), findsOneWidget);
  });

  testWidgets(
    'forgot password gives the same reply whether or not the account exists',
    (tester) async {
      final repository = FakeAuthRepository();
      await _pumpApp(tester, repository);
      await tester.tap(find.widgetWithText(OutlinedButton, 'Sign in'));
      await _settle(tester);
      await tester.tap(find.text('Forgot password?'));
      await _settle(tester);

      await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'),
        'nobody@example.com',
      );
      await tester.tap(find.widgetWithText(FilledButton, 'Send reset code'));
      await _settle(tester);

      expect(repository.resetRequests, ['nobody@example.com']);
      expect(
        find.text(
          'If an account exists for that email, we have sent a reset code to it.',
        ),
        findsOneWidget,
      );
    },
  );

  testWidgets('a wrong reset code is refused and the form stays open', (
    tester,
  ) async {
    await _pumpApp(tester, FakeAuthRepository());
    await tester.tap(find.widgetWithText(OutlinedButton, 'Sign in'));
    await _settle(tester);
    await tester.tap(find.text('Forgot password?'));
    await _settle(tester);
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Email'),
      'shopper@example.com',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Send reset code'));
    await _settle(tester);
    await tester.tap(find.widgetWithText(FilledButton, 'Enter reset code'));
    await _settle(tester);

    await tester.enterText(
      find.widgetWithText(TextFormField, 'Reset code'),
      'wrong-code-value',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'New password'),
      'a brand new passphrase',
    );
    await tester.enterText(
      find.widgetWithText(TextFormField, 'Confirm new password'),
      'a brand new passphrase',
    );
    await tester.tap(find.widgetWithText(FilledButton, 'Update password'));
    await _settle(tester);

    expect(
      find.text('This reset link is invalid or has expired.'),
      findsOneWidget,
    );
    expect(find.text('Set a new password'), findsOneWidget);
  });
}
