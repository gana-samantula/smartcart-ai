import 'package:material_ui/material_ui.dart';
import 'package:smartcart_app/common/widgets/coming_soon_view.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: ComingSoonView(
        title: 'Settings are coming soon',
        description: 'Profile, privacy and subscription settings arrive in Phase 2 and Phase 9.',
      ),
    );
  }
}
