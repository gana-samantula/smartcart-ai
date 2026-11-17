import 'package:material_ui/material_ui.dart';
import 'package:smartcart_app/common/widgets/coming_soon_view.dart';

class ListsScreen extends StatelessWidget {
  const ListsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: ComingSoonView(
        title: 'Shopping lists are coming soon',
        description: 'Create lists and compare basket prices in Phase 7.',
      ),
    );
  }
}
