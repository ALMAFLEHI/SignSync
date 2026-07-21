import 'package:flutter/material.dart';

import '../../theme/signsync_theme.dart';

class SignSyncLogo extends StatelessWidget {
  const SignSyncLogo({super.key, this.size = 52});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: 'SignSync logo',
      image: true,
      child: CustomPaint(
        key: const ValueKey('signsync-logo-mark'),
        size: Size.square(size),
        painter: const _SignSyncLogoPainter(),
      ),
    );
  }
}

class SignSyncWordmark extends StatelessWidget {
  const SignSyncWordmark({super.key, this.markSize = 40, this.textStyle});

  final double markSize;
  final TextStyle? textStyle;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        SignSyncLogo(size: markSize),
        const SizedBox(width: 10),
        Text(
          'SignSync',
          style:
              textStyle ??
              Theme.of(context).textTheme.titleLarge?.copyWith(
                color: Theme.of(context).colorScheme.onSurface,
                fontWeight: FontWeight.w800,
              ),
        ),
      ],
    );
  }
}

class _SignSyncLogoPainter extends CustomPainter {
  const _SignSyncLogoPainter();

  @override
  void paint(Canvas canvas, Size size) {
    final scale = size.shortestSide / 64;
    final bounds = Offset.zero & size;
    final background = Paint()..color = SignSyncTheme.navy;
    canvas.drawRRect(
      RRect.fromRectAndRadius(bounds, Radius.circular(14 * scale)),
      background,
    );

    final connection = Path()
      ..moveTo(18 * scale, 20 * scale)
      ..cubicTo(
        26 * scale,
        12 * scale,
        42 * scale,
        14 * scale,
        45 * scale,
        22 * scale,
      )
      ..cubicTo(
        48 * scale,
        30 * scale,
        36 * scale,
        31 * scale,
        29 * scale,
        34 * scale,
      )
      ..cubicTo(
        20 * scale,
        37 * scale,
        17 * scale,
        44 * scale,
        23 * scale,
        49 * scale,
      )
      ..cubicTo(
        29 * scale,
        54 * scale,
        42 * scale,
        50 * scale,
        46 * scale,
        44 * scale,
      );
    canvas.drawPath(
      connection,
      Paint()
        ..color = const Color(0xFF59D4CC)
        ..style = PaintingStyle.stroke
        ..strokeWidth = 6 * scale
        ..strokeCap = StrokeCap.round,
    );

    final textPaint = Paint()
      ..color = Colors.white
      ..strokeWidth = 2.4 * scale
      ..strokeCap = StrokeCap.round;
    canvas.drawLine(
      Offset(35 * scale, 39 * scale),
      Offset(46 * scale, 39 * scale),
      textPaint,
    );
    canvas.drawLine(
      Offset(37 * scale, 44 * scale),
      Offset(43 * scale, 44 * scale),
      textPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
