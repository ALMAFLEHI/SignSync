import 'package:flutter/material.dart';
import 'package:flutter_app/models/sign_mode.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/widgets/mode_selector.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('historical modes remain visible but disabled in dark mode', (
    tester,
  ) async {
    var selectedMode = SignMode.bankingIntent;
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        darkTheme: SignSyncTheme.dark,
        themeMode: ThemeMode.dark,
        home: StatefulBuilder(
          builder: (context, setState) => Scaffold(
            body: ModeSelector(
              selectedMode: selectedMode,
              onChanged: (mode) => setState(() => selectedMode = mode),
            ),
          ),
        ),
      ),
    );

    final numberOption = find.byKey(const ValueKey('mode-option-number'));
    final bankingOption = find.byKey(
      const ValueKey('mode-option-bankingIntent'),
    );
    final numberInkWell = tester.widget<InkWell>(
      find.descendant(of: numberOption, matching: find.byType(InkWell)),
    );
    final bankingInkWell = tester.widget<InkWell>(
      find.descendant(of: bankingOption, matching: find.byType(InkWell)),
    );

    expect(numberInkWell.onTap, isNull);
    expect(bankingInkWell.onTap, isNotNull);
    expect(
      find.text('Historical mode unavailable with the final 40-class model'),
      findsNWidgets(2),
    );
    await tester.tap(numberOption);
    await tester.pump();
    expect(selectedMode, SignMode.bankingIntent);
  });

  testWidgets('banking intent remains the only enabled light-mode option', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        home: Scaffold(
          body: ModeSelector(
            selectedMode: SignMode.bankingIntent,
            onChanged: (_) {},
          ),
        ),
      ),
    );

    final alphabetOption = find.byKey(const ValueKey('mode-option-alphabet'));
    final alphabetInkWell = tester.widget<InkWell>(
      find.descendant(of: alphabetOption, matching: find.byType(InkWell)),
    );
    final bankingOption = find.byKey(
      const ValueKey('mode-option-bankingIntent'),
    );
    final selectedMaterial = tester.widget<Material>(bankingOption);
    final colors = Theme.of(tester.element(bankingOption)).colorScheme;

    expect(alphabetInkWell.onTap, isNull);
    expect(selectedMaterial.color, colors.primaryContainer);
    expect(
      find.descendant(
        of: bankingOption,
        matching: find.text('Final 40 banking intents'),
      ),
      findsOneWidget,
    );
  });
}
