import 'package:flutter/material.dart';
import 'package:flutter_app/app/signsync_app.dart';
import 'package:flutter_app/theme/app_theme_preference.dart';
import 'package:flutter_app/theme/theme_controller.dart';
import 'package:flutter_app/theme/theme_preference_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'theme controller loads and persists a non-sensitive preference',
    () async {
      final store = _MemoryThemeStore(AppThemePreference.dark);
      final controller = ThemeController(store: store);
      addTearDown(controller.dispose);

      await controller.load();
      expect(controller.preference, AppThemePreference.dark);
      expect(controller.preference.themeMode, ThemeMode.dark);

      final pendingWrite = controller.setPreference(AppThemePreference.light);
      expect(controller.preference, AppThemePreference.light);
      expect(controller.preference.themeMode, ThemeMode.light);
      await pendingWrite;
      expect(store.writes, <AppThemePreference>[AppThemePreference.light]);
    },
  );

  testWidgets(
    'Settings offers System, Light, and Dark and changes immediately',
    (tester) async {
      final store = _MemoryThemeStore(AppThemePreference.system);
      final controller = ThemeController(store: store);
      addTearDown(controller.dispose);
      await tester.pumpWidget(SignSyncApp(themeController: controller));
      await tester.tap(find.byTooltip('Settings'));
      await tester.pumpAndSettle();

      expect(find.text('System'), findsOneWidget);
      expect(find.text('Light'), findsOneWidget);
      expect(find.text('Dark'), findsOneWidget);
      await tester.tap(find.text('Dark'));
      await tester.pump();

      expect(controller.preference, AppThemePreference.dark);
      expect(
        tester.widget<MaterialApp>(find.byType(MaterialApp)).themeMode,
        ThemeMode.dark,
      );
      await tester.pumpAndSettle();
      expect(store.writes, contains(AppThemePreference.dark));
    },
  );

  test('SharedPreferences store writes only the theme key', () async {
    SharedPreferences.setMockInitialValues(<String, Object>{});
    final store = SharedPreferencesThemePreferenceStore();

    await store.write(AppThemePreference.dark);
    final preferences = await SharedPreferences.getInstance();

    expect(preferences.getKeys(), <String>{
      SharedPreferencesThemePreferenceStore.preferenceKey,
    });
    expect(await store.read(), AppThemePreference.dark);
  });
}

class _MemoryThemeStore implements ThemePreferenceStore {
  _MemoryThemeStore(this.value);

  AppThemePreference value;
  final List<AppThemePreference> writes = <AppThemePreference>[];

  @override
  Future<AppThemePreference> read() async => value;

  @override
  Future<void> write(AppThemePreference preference) async {
    value = preference;
    writes.add(preference);
  }
}
