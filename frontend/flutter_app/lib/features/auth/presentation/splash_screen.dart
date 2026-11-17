import 'package:material_ui/material_ui.dart';

/// Shown while the stored session is checked. Routing moves on once the check finishes.
class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Semantics(label: 'Loading', child: CircularProgressIndicator()),
      ),
    );
  }
}
