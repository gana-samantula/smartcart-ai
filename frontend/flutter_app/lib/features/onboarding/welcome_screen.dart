import 'package:go_router/go_router.dart';
import 'package:material_ui/material_ui.dart';

/// First screen for signed-out users. Choosing either button leads to a working form.
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              Text('SmartCart AI', style: theme.textTheme.headlineMedium),
              const SizedBox(height: 12),
              Text(
                'Know what you pay for groceries. Scan a receipt, track prices across stores, '
                'and find the cheapest place to buy your list.',
                style: theme.textTheme.bodyLarge,
              ),
              const Spacer(),
              FilledButton(
                onPressed: () => context.go('/register'),
                child: const Text('Create account'),
              ),
              const SizedBox(height: 12),
              OutlinedButton(
                onPressed: () => context.go('/login'),
                child: const Text('Sign in'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
