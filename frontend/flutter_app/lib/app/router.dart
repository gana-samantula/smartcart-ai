import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:smartcart_app/app/main_shell.dart';
import 'package:smartcart_app/features/auth/application/auth_controller.dart';
import 'package:smartcart_app/features/auth/presentation/forgot_password_screen.dart';
import 'package:smartcart_app/features/auth/presentation/login_screen.dart';
import 'package:smartcart_app/features/auth/presentation/register_screen.dart';
import 'package:smartcart_app/features/auth/presentation/reset_password_screen.dart';
import 'package:smartcart_app/features/auth/presentation/splash_screen.dart';
import 'package:smartcart_app/features/catalog/catalog_screen.dart';
import 'package:smartcart_app/features/home/home_screen.dart';
import 'package:smartcart_app/features/lists/lists_screen.dart';
import 'package:smartcart_app/features/onboarding/welcome_screen.dart';
import 'package:smartcart_app/features/receipts/receipts_screen.dart';
import 'package:smartcart_app/features/settings/settings_screen.dart';

/// Screens a signed-out user may open. Everything else requires a session.
const Set<String> publicRoutes = {
  '/welcome',
  '/login',
  '/register',
  '/forgot-password',
  '/reset-password',
};

/// Where to send the user for [auth], or null to stay where they are.
@visibleForTesting
String? redirectFor(AuthState auth, String location) {
  switch (auth.status) {
    case AuthStatus.unknown:
      return location == '/splash' ? null : '/splash';
    case AuthStatus.signedOut:
      return publicRoutes.contains(location) ? null : '/welcome';
    case AuthStatus.signedIn:
      final leavingSignIn =
          location == '/splash' || publicRoutes.contains(location);
      return leavingSignIn ? '/home' : null;
  }
}

/// Builds the application router. Each tab keeps its own navigation stack.
GoRouter buildRouter({
  required Listenable refreshListenable,
  required AuthState Function() currentAuth,
}) {
  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refreshListenable,
    redirect: (context, state) =>
        redirectFor(currentAuth(), state.matchedLocation),
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/welcome',
        builder: (context, state) => const WelcomeScreen(),
      ),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/forgot-password',
        builder: (context, state) => const ForgotPasswordScreen(),
      ),
      GoRoute(
        path: '/reset-password',
        builder: (context, state) => const ResetPasswordScreen(),
      ),
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) =>
            MainShell(navigationShell: navigationShell),
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/home',
                builder: (context, state) => const HomeScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/receipts',
                builder: (context, state) => const ReceiptsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/lists',
                builder: (context, state) => const ListsScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/catalog',
                builder: (context, state) => const CatalogScreen(),
              ),
            ],
          ),
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/settings',
                builder: (context, state) => const SettingsScreen(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
}

/// The router lives in a provider so it is created once per app and disposed with it.
/// It re-checks redirects whenever the auth state changes.
final routerProvider = Provider<GoRouter>((ref) {
  final refresh = ValueNotifier<int>(0);
  ref.listen<AuthState>(
    authControllerProvider,
    (previous, next) => refresh.value++,
  );
  final router = buildRouter(
    refreshListenable: refresh,
    currentAuth: () => ref.read(authControllerProvider),
  );
  ref.onDispose(() {
    router.dispose();
    refresh.dispose();
  });
  return router;
});
