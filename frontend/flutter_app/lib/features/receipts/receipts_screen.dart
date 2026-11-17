import 'package:material_ui/material_ui.dart';
import 'package:smartcart_app/common/widgets/coming_soon_view.dart';

class ReceiptsScreen extends StatelessWidget {
  const ReceiptsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: ComingSoonView(
        title: 'Receipts are coming soon',
        description:
            'Receipt capture and review arrive in Phase 3 and Phase 4.',
      ),
    );
  }
}
