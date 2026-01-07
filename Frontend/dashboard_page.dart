import 'package:flutter/material.dart';
import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:mjpeg_stream/mjpeg_stream.dart';

import 'config.dart';

class DashboardPage extends StatefulWidget {
  final String role;
  const DashboardPage({super.key, required this.role});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  List<dynamic> notifications = [];
  bool loading = false;
  Timer? _timer;

  Future<void> fetchNotifications() async {
    try {
      final res = await http.get(Uri.parse(AppConfig.notifyUrl));
      if (res.statusCode == 200) {
        if (!mounted) return;
        setState(() {
          notifications = jsonDecode(res.body);
        });
      }
    } catch (_) {}
  }

  Future<void> takePhoto() async {
    if (widget.role != "admin") return;
    setState(() => loading = true);

    try {
      final res = await http.post(Uri.parse(AppConfig.takePhotoUrl));
      if (!mounted) return;

      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text("Photo sent successfully"),
          backgroundColor: Colors.green,
        ));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text("Failed to send photo"),
          backgroundColor: Colors.redAccent,
        ));
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> clearNotifications() async {
    if (widget.role != "admin") return;
    await http.post(
      Uri.parse(AppConfig.clearUrl),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode({"role": widget.role}),
    );
    fetchNotifications();
  }

  @override
  void initState() {
    super.initState();
    fetchNotifications();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => fetchNotifications());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Widget _buildStreamBox() {
    return Container(
      height: 200,
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: Colors.black,
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            blurRadius: 8,
            offset: Offset(0, 4),
            color: Colors.black26,
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: MJPEGStreamScreen(
        streamUrl: AppConfig.streamUrl,
        width: double.infinity,
        height: 200,
        fit: BoxFit.cover,
        showLiveIcon: false,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final reversed = notifications.reversed.toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text("Robot Dashboard"),
        backgroundColor: Colors.indigo,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => Navigator.pop(context),
          ),
        ],
      ),
      body: Container(
        color: const Color(0xFFF5F7FA),
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildStreamBox(),

            if (widget.role == "admin")
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: [
                    ElevatedButton.icon(
                      onPressed: loading ? null : takePhoto,
                      icon: const Icon(Icons.camera_alt),
                      label: const Text("Take Photo"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.indigo,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton.icon(
                      onPressed: clearNotifications,
                      icon: const Icon(Icons.delete_forever),
                      label: const Text("Clear Logs"),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.redAccent,
                        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                      ),
                    ),
                  ],
                ),
              ),

            const SizedBox(height: 20),

            Expanded(
              child: reversed.isEmpty
                  ? const Center(child: Text("No notifications yet"))
                  : ListView.builder(
                      itemCount: reversed.length,
                      itemBuilder: (context, i) {
                        final n = reversed[i];
                        final title = (n["title"] ?? "").toString();

                        IconData icon = Icons.warning;
                        Color color = Colors.grey;

                        if (title.contains("Gas")) {
                          icon = Icons.local_fire_department;
                          color = Colors.redAccent;
                        } else if (title.contains("Water")) {
                          icon = Icons.water_drop;
                          color = Colors.blueAccent;
                        }

                        return Card(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          margin: const EdgeInsets.symmetric(vertical: 8),
                          child: ListTile(
                            leading: Icon(icon, color: color, size: 32),
                            title: Text(
                              title,
                              style: const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            subtitle: Text("${n["message"]}\n${n["time"]}"),
                            isThreeLine: true,
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
}
