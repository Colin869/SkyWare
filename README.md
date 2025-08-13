# WiiWare Modder v1.1

A comprehensive Windows application for modding WiiWare software, games, and tools. This application provides an intuitive graphical interface for working with WiiWare files and managing mods.

## ✨ New in Version 1.1

### 🔧 File Patching Capabilities
- Apply IPS, BPS, and custom patch files to WiiWare files
- Automatic backup creation before patching
- Patch validation and compatibility checking
- Complete patch history tracking
- Patch reversion capabilities

### 📦 Batch Processing for Multiple Files
- Process multiple WiiWare files simultaneously
- Support for extraction, patching, and analysis operations
- Progress tracking for batch operations
- Configurable output directories
- Error handling and logging

### 🛠️ Enhanced Mod Installation System
- Advanced mod compatibility validation
- Automatic backup creation
- Mod metadata tracking
- Comprehensive mod management interface
- Mod information display and configuration

### 🎨 **NEW!** Professional User Experience
- **Comprehensive Logging System**: Detailed logging to files and console
- **User Preferences**: Persistent settings between sessions
- **Recent Files**: Quick access to recently opened files
- **Settings Dialog**: Comprehensive configuration options
- **Progress Tracking**: Real-time operation progress with callbacks
- **Theme Support**: Multiple GUI themes (clam, alt, default, classic)
- **Window Memory**: Remembers window position and size

## 🎮 Features

### File Management
- Browse and select WiiWare files (.wad, .wbfs, .iso)
- File information display and analysis
- Integration with the WIT tool for detailed file information
- **NEW!** Recent files menu for quick access
- **NEW!** Smart directory memory for file dialogs

### Extraction Tools
- Extract WiiWare files using the WIT tool
- Progress tracking during extraction
- Configurable output directories
- **NEW!** Enhanced progress reporting with callbacks

### File Patching
- **NEW!** Apply various patch formats (IPS, BPS, custom)
- **NEW!** Automatic backup creation
- **NEW!** Patch validation and history tracking
- **NEW!** Patch reversion capabilities

### Batch Processing
- **NEW!** Process multiple files simultaneously
- **NEW!** Multiple operation types (extract, patch, analyze)
- **NEW!** Progress tracking and status updates
- **NEW!** Configurable batch options

### Enhanced Modding Tools
- **ENHANCED!** Advanced mod installation with validation
- **ENHANCED!** Automatic backup creation
- **ENHANCED!** Mod compatibility checking
- **ENHANCED!** Comprehensive mod management
- **ENHANCED!** Mod information and configuration

### BrawlCrate Integration
- **NEW!** Direct integration with BrawlCrate for game file analysis
- **NEW!** Support for BRRES, BRLYT, BRLAN, BRSEQ, BRSTM, BRWAV, and BRCTMD files
- **NEW!** Automatic file type detection and analysis
- **NEW!** Launch files directly in BrawlCrate for editing
- **NEW!** Export analysis results for documentation

### Community Features
- Browse community mod library
- Upload and share mods
- Check for application updates

### **NEW!** Professional Features
- **Comprehensive Logging**: All operations logged to `logs/wiiware_modder.log`
- **User Preferences**: Settings saved in `user_preferences.json`
- **Progress Callbacks**: Real-time progress updates for all operations
- **Settings Dialog**: Easy access to all configuration options
- **Theme System**: Multiple GUI themes with live preview
- **Error Handling**: Robust error handling with user-friendly messages
- **Threading Safety**: All long operations run in background threads

## Prerequisites

### Required Software
- **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
- **WIT Tool** - Wii ISO Tools for file manipulation

### Installing WIT Tool
1. Download WIT from the official repository
2. Extract to a directory (e.g., `C:\Program Files\wit\`)
3. Add the directory to your system PATH, or place `wit.exe` in the same directory as this application

## Installation

1. **Clone or download** this repository
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Getting Started
1. Launch the application
2. Click "Browse" to select a WiiWare file (.wad, .wbfs, .iso)
3. The application will automatically analyze the file and display information

### **NEW!** Enhanced User Experience
1. **Recent Files**: Use the "Recent Files" button to quickly access recently opened files
2. **Settings**: Click the "⚙️ Settings" button to configure application preferences
3. **Progress Tracking**: Monitor real-time progress for all operations
4. **Theme Selection**: Choose from multiple GUI themes in the settings

### File Operations
- **File Info Tab**: View detailed information about selected files
- **Extraction Tab**: Extract WiiWare files with progress tracking
- **Patching Tab**: Apply patches with automatic backup creation
- **Batch Processing Tab**: Process multiple files simultaneously
- **Modding Tab**: Install and manage mods with validation
- **BrawlCrate Tab**: Analyze and edit game files
- **Community Tab**: Access community features

### **NEW!** Settings Configuration
- **General**: Configure auto-backup, mod validation, and operation confirmations
- **Interface**: Choose themes and set default window sizes
- **Backup**: Configure backup directories and settings

## Project Structure

```
wiiware mods/
├── main.py                 # Main application file
├── config.ini             # Application configuration
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── run.bat                # Windows batch launcher
├── run.ps1                # PowerShell launcher
├── test_features.py       # Comprehensive unit tests
├── user_preferences.json  # User settings (created automatically)
├── logs/                  # Application logs
├── backups/               # File backups
├── mods/                  # Installed mods
├── patches/               # Patch files
├── batch_output/          # Batch processing output
└── brawlcrate/            # BrawlCrate integration files
```

## **NEW!** Advanced Features

### Logging System
The application maintains comprehensive logs in the `logs/` directory:
- **File**: `logs/wiiware_modder.log`
- **Level**: DEBUG, INFO, WARNING, ERROR
- **Format**: Timestamp, level, message
- **Console**: Important messages displayed in console

### User Preferences
User settings are automatically saved and restored:
- Window position and size
- Theme selection
- Directory preferences
- Operation settings
- Recent files list

### Progress Tracking
All operations provide real-time progress updates:
- Progress bars with percentage
- Status messages
- Operation completion notifications
- Background threading for responsiveness

### Settings Management
Comprehensive settings dialog with:
- General application settings
- Interface customization
- Backup configuration
- Theme selection
- Window preferences

## Testing

### Running Tests
```bash
python test_features.py
```

### Test Coverage
The comprehensive test suite covers:
- ✅ Directory creation and management
- ✅ User preferences system
- ✅ Logging system
- ✅ File operations and validation
- ✅ Patch system functionality
- ✅ Mod management
- ✅ Batch processing
- ✅ BrawlCrate integration
- ✅ Backup system
- ✅ Configuration system
- ✅ Error handling
- ✅ Progress tracking
- ✅ File type validation
- ✅ Threading safety
- ✅ Memory management
- ✅ UI element validation
- ✅ Application integration

## Development

### Adding New Features
1. **Follow the existing pattern** for new tabs and functionality
2. **Add logging** for all operations using the logger
3. **Update user preferences** if new settings are added
4. **Add progress tracking** for long operations
5. **Include error handling** for all file operations
6. **Add unit tests** for new functionality

### Code Standards
- Use comprehensive error handling
- Implement progress callbacks for long operations
- Add logging for debugging and monitoring
- Follow the existing GUI patterns
- Include user preference options where appropriate

### Testing Guidelines
- Run the test suite after making changes
- Add new tests for new features
- Ensure all tests pass before committing
- Test error conditions and edge cases

## Troubleshooting

### Common Issues

#### Application Won't Start
- Ensure Python 3.7+ is installed
- Check that all dependencies are installed
- Verify the `main.py` file is in the correct directory

#### WIT Tool Not Found
- Install the WIT tool from the official repository
- Add WIT to your system PATH
- Or place `wit.exe` in the application directory

#### **NEW!** Logging Issues
- Check the `logs/` directory exists
- Verify write permissions for the application directory
- Check console output for error messages

#### **NEW!** Preferences Not Saving
- Ensure the application has write permissions
- Check that `user_preferences.json` is not read-only
- Verify the application directory is writable

#### **NEW!** Theme Not Applying
- Check that the selected theme is available
- Verify the theme name is correct (clam, alt, default, classic)
- Restart the application after theme changes

### Getting Help
1. Check the application logs in `logs/wiiware_modder.log`
2. Review the console output for error messages
3. Verify all required directories exist and are writable
4. Check that Python dependencies are properly installed

## Roadmap

### ✅ Version 1.1 (Completed)
- File Patching Capabilities
- Batch Processing for Multiple Files
- Enhanced Mod Installation System
- BrawlCrate Integration
- **NEW!** Comprehensive Logging System
- **NEW!** User Preferences and Settings
- **NEW!** Progress Tracking and Callbacks
- **NEW!** Professional User Experience
- **NEW!** Comprehensive Unit Testing

### 🚧 Version 1.2 (In Development)
- Advanced patch formats support
- Mod dependency management
- Community mod repository integration
- Enhanced file validation
- Performance optimizations

### 🔮 Version 2.0 (Planned)
- Plugin system for extensibility
- Advanced mod creation tools
- Network features for mod sharing
- Cross-platform support
- Advanced debugging tools

## Contributing

### How to Contribute
1. **Fork the repository**
2. **Create a feature branch** for your changes
3. **Follow the coding standards** and patterns
4. **Add comprehensive tests** for new features
5. **Update documentation** as needed
6. **Submit a pull request** with detailed description

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `python test_features.py`
4. Make your changes
5. Ensure all tests pass
6. Update documentation

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- **WIT Tool** developers for Wii file manipulation
- **BrawlCrate** team for game file analysis tools
- **Python community** for excellent libraries and tools
- **WiiWare modding community** for inspiration and feedback

---

**🎉 Your WiiWare Modder application is now a professional-grade tool with comprehensive logging, user preferences, progress tracking, and robust error handling!**
