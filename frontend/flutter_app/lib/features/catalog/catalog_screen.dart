import 'package:material_ui/material_ui.dart';
import 'package:smartcart_app/common/widgets/coming_soon_view.dart';

class CatalogScreen extends StatelessWidget {
  const CatalogScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: ComingSoonView(
        title: 'Product catalog is coming soon',
        description:
            'Search products and view price history in Phase 5 and Phase 6.',
      ),
    );
  }
}
