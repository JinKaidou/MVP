// lib/screens/map_screen.dart
import 'package:flutter/material.dart';

class MapScreen extends StatelessWidget {
  final Color themeColor;

  const MapScreen({super.key, this.themeColor = const Color(0xFF2D7CFF)});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Campus Map',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        backgroundColor: themeColor,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Container(
        color: Colors.white,
        child: InteractiveViewer(
          boundaryMargin: const EdgeInsets.all(20.0),
          minScale: 0.5,
          maxScale: 4.0,
          child: Center(
            child: Image.asset(
              'assets/images/USTP.png',
              fit: BoxFit.contain,
              errorBuilder: (context, error, stackTrace) {
                return Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(
                      Icons.error_outline,
                      color: themeColor.withOpacity(0.8),
                      size: 48,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Error loading map: ${error.toString()}',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: themeColor.withOpacity(0.8)),
                    ),
                  ],
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}
