import 'package:flutter/material.dart';
import 'package:flutter_app/config/phone_dataset_scope.dart';
import 'package:flutter_app/theme/signsync_theme.dart';
import 'package:flutter_app/ui/live_camera_page.dart';
import 'package:flutter_app/ui/phone_dataset_collection_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'shows exactly the 36 remaining labels and protected pilot summary',
    (tester) async {
      await tester.pumpWidget(
        const MaterialApp(home: PhoneDatasetCollectionPage()),
      );
      await tester.pumpAndSettle();

      expect(
        find.text('Sprint 2.16B Full Banking Intent Expansion'),
        findsOneWidget,
      );
      expect(find.text('Sprint 2.16A Completed (Protected)'), findsOneWidget);
      expect(find.text('0 / 900'), findsOneWidget);
      expect(find.text('0 / 36'), findsOneWidget);
      for (final label in PhoneDatasetScope.sprint216APilotIntents) {
        expect(find.text(label), findsOneWidget);
      }
      await _showLabelSelector(tester);
      for (final label in PhoneDatasetScope.sprint216BRemainingBankingIntents) {
        expect(find.text(label), findsOneWidget);
      }
    },
  );

  testWidgets('requires confirmation before changing the selected label', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(home: PhoneDatasetCollectionPage()),
    );
    await tester.pumpAndSettle();
    await _showLabelSelector(tester);
    final withdrawLabel = find.text('withdraw');
    await tester.ensureVisible(withdrawLabel);
    await tester.tap(withdrawLabel);
    await tester.pumpAndSettle();

    expect(find.text('Change collection label?'), findsOneWidget);
    expect(
      find.textContaining('Move from deposit to withdraw?'),
      findsOneWidget,
    );
    await tester.tap(find.text('Change Label'));
    await tester.pumpAndSettle();

    await tester.scrollUntilVisible(
      find.text('Selected withdraw.'),
      -400,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();

    expect(find.text('Selected withdraw.'), findsOneWidget);
  });

  testWidgets('matches the final live diagnostics portrait preview contract', (
    tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: LiveCameraPage()));
    await tester.pump();

    final livePreview = tester.widget<AspectRatio>(
      find.byType(AspectRatio).first,
    );
    expect(livePreview.aspectRatio, 3 / 4);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pump();
    await tester.pumpWidget(
      const MaterialApp(home: PhoneDatasetCollectionPage()),
    );
    await tester.pumpAndSettle();

    await tester.drag(find.byType(Scrollable).first, const Offset(0, -500));
    await tester.pumpAndSettle();

    final previewFinder = find.byKey(
      PhoneDatasetCollectionPage.cameraPreviewKey,
    );
    expect(previewFinder, findsOneWidget);

    final preview = tester.widget<AspectRatio>(previewFinder);
    expect(
      preview.aspectRatio,
      PhoneDatasetCollectionPage.cameraPreviewAspectRatio,
    );
    expect(preview.aspectRatio, livePreview.aspectRatio);
    expect(preview.aspectRatio, 3 / 4);
  });

  testWidgets('places capture status and controls before label selection', (
    tester,
  ) async {
    tester.view.devicePixelRatio = 1;
    tester.view.physicalSize = const Size(800, 3000);
    addTearDown(tester.view.resetDevicePixelRatio);
    addTearDown(tester.view.resetPhysicalSize);

    await tester.pumpWidget(
      const MaterialApp(home: PhoneDatasetCollectionPage()),
    );
    await tester.pumpAndSettle();

    final previewTop = tester
        .getTopLeft(find.byKey(PhoneDatasetCollectionPage.cameraPreviewKey))
        .dy;
    final statusTop = tester.getTopLeft(find.text('Sample Capture Status')).dy;
    final controlsTop = tester.getTopLeft(find.text('Start Camera')).dy;
    final labelsTop = tester
        .getTopLeft(find.text('Remaining Banking Intent'))
        .dy;

    expect(previewTop, lessThan(statusTop));
    expect(statusTop, lessThan(controlsTop));
    expect(controlsTop, lessThan(labelsTop));
  });

  testWidgets('dark theme keeps collection rows readable and selectable', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: SignSyncTheme.light,
        darkTheme: SignSyncTheme.dark,
        themeMode: ThemeMode.dark,
        home: const PhoneDatasetCollectionPage(),
      ),
    );
    await tester.pumpAndSettle();
    await _showLabelSelector(tester);

    final selected = find.byKey(const ValueKey('collection-label-deposit'));
    final unselected = find.byKey(const ValueKey('collection-label-withdraw'));
    final colors = Theme.of(tester.element(unselected)).colorScheme;
    final unselectedMaterial = tester.widget<Material>(unselected);
    final unselectedTitle = tester.widget<Text>(
      find.descendant(of: unselected, matching: find.text('withdraw')),
    );
    final counter = tester.widget<Text>(
      find.descendant(of: unselected, matching: find.text('0 / 25')),
    );
    final remaining = tester.widget<Text>(
      find.descendant(of: unselected, matching: find.text('25 left')),
    );
    final inkWell = tester.widget<InkWell>(
      find.descendant(of: unselected, matching: find.byType(InkWell)),
    );

    expect(unselectedMaterial.color, colors.surfaceContainerHigh);
    expect(unselectedMaterial.color, isNot(Colors.white));
    expect(unselectedTitle.style?.color, colors.onSurface);
    expect(counter.style?.color, colors.onSurface);
    expect(remaining.style?.color, colors.onSurfaceVariant);
    expect(inkWell.onTap, isNotNull);

    final selectedMaterial = tester.widget<Material>(selected);
    final selectedTitle = tester.widget<Text>(
      find.descendant(of: selected, matching: find.text('deposit')),
    );
    expect(selectedMaterial.color, colors.primaryContainer);
    expect(selectedTitle.style?.color, colors.onPrimaryContainer);
  });
}

Future<void> _showLabelSelector(WidgetTester tester) async {
  await tester.scrollUntilVisible(
    find.text('Remaining Banking Intent'),
    400,
    scrollable: find.byType(Scrollable).first,
  );
  await tester.pumpAndSettle();
}
