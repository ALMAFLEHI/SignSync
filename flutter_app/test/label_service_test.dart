import 'package:flutter_app/config/app_config.dart';
import 'package:flutter_app/services/label_service.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('loads and validates Sprint 2.13 label metadata assets', () async {
    final metadata = await LabelService().load();

    expect(metadata.labels, hasLength(AppConfig.expectedOutputClasses));
    expect(
      metadata.normalModeLabels,
      hasLength(AppConfig.expectedNormalModeLabels),
    );
    expect(
      metadata.numberModeLabels,
      hasLength(AppConfig.expectedNumberModeLabels),
    );
  });
}
