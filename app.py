import sys
import threading
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QGroupBox,
    QScrollArea,
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QFont, QFontDatabase, QColor
from PyQt5.QtCore import QTimer, pyqtSignal

from api import generate_article_outline, generate_full_article_from_outline


class ArticleGenerator(QWidget):

    """
    A PyQt5-based GUI application for generating articles using OpenAI's GPT model.

    This class creates an interface where users can input article titles, tags, and notes,
    and receive a generated article based on these inputs. The class uses threading to
    handle the API requests asynchronously, ensuring the GUI remains responsive.

    Attributes:
    articleGenerated (pyqtSignal): Signal emitted when the article is generated.
    generated_text (str): String to hold the generated article text.
    ellipsis_timer (QTimer): Timer for the ellipsis animation during loading.
    ellipsis_count (int): Counter to keep track of the ellipsis animation state.
    typing_timer (QTimer): Timer for simulating the typing effect of the article text.
    """

    articleGenerated = pyqtSignal(str)

    def __init__(self):
        """
        Constructor for the ArticleGenerator class. Initializes the UI and timers.
        """
        super().__init__()
        self.init_ui()  # Initialize the user interface components
        self.generated_text = ""  # Placeholder for the generated article text

        # Initialize a QTimer for creating an ellipsis animation during loading
        self.ellipsis_timer = QTimer()
        self.ellipsis_timer.timeout.connect(self.update_ellipsis)
        self.ellipsis_count = 0

        # Connect the generated article signal to the GUI update function
        self.articleGenerated.connect(self.update_gui_with_generated_article)

        # Initialize a QTimer for simulating the typing effect in the text display
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_character)

    def init_ui(self):
        """
        Initialize the user interface components of the application.

        This method sets up the main layout, creates the left and right layouts,
        and adds them to a splitter for a resizable interface. It also sets the
        window title and size.
        """

        self.setup_styles()  # Set up styles and shared resources
        self.setWindowTitle("DevQuine")
        self.setGeometry(100, 100, 1200, 700)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)

        left_layout = self.create_left_layout()
        right_layout = self.create_right_layout()

        splitter = QSplitter()
        splitter.addWidget(self.create_widget(left_layout))
        splitter.addWidget(self.create_widget(right_layout))
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def setup_styles(self):
        self.FONT_COLOR = QColor("#FFFFFF")
        self.INPUT_BOX_COLOR = QColor("#303030")
        self.BACKGROUND_COLOR = QColor("#1F1F1F")
        self.BUTTON_COLOR = QColor("#2196F3")

        self.setStyleSheet(
            f"background-color: {self.BACKGROUND_COLOR.name()}; color: {self.FONT_COLOR.name()}"
        )

    def create_shadow_effect(self):
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(150)
        shadow_effect.setXOffset(5)
        shadow_effect.setYOffset(5)
        shadow_effect.setColor(QColor(0, 0, 0, 60))
        return shadow_effect

    def create_input_style(self):
        return """
        QLineEdit, QTextEdit {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
            background-color: %s;
            color: %s;
        }
        """ % (
            self.INPUT_BOX_COLOR.name(),
            self.FONT_COLOR.name(),
        )

    def create_button_style(self):
        return """
        QPushButton {
            background-color: %s;
            color: %s;
            border-radius: 20px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #0a7aca;
        }
        """ % (
            self.BUTTON_COLOR.name(),
            self.FONT_COLOR.name(),
        )

    def create_left_layout(self):
        """
        Create the left layout of the GUI.

        This layout includes input fields for the article title, tags, and notes,
        as well as a button to trigger the article generation process. Each input
        field and the button are styled and added to the layout.
        """

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(10, 20, 10, 20)
        left_layout.setSpacing(20)

        # Create and add the title label and entry
        title_label = QLabel("Article Title:")
        title_label.setFont(QFont("Arial", 16))
        title_label.setStyleSheet(f"color: {self.FONT_COLOR.name()}")
        left_layout.addWidget(title_label)

        self.title_entry = QLineEdit()
        self.title_entry.setFont(QFont("Arial", 16))
        self.title_entry.setStyleSheet(self.create_input_style())
        self.title_entry.setGraphicsEffect(self.create_shadow_effect())
        left_layout.addWidget(self.title_entry)

        # Create and add the tags label and entry
        tags_label = QLabel("Tags (separated by commas):")
        tags_label.setFont(QFont("Arial", 16))
        tags_label.setStyleSheet(f"color: {self.FONT_COLOR.name()}")
        left_layout.addWidget(tags_label)

        self.tags_entry = QLineEdit()
        self.tags_entry.setFont(QFont("Arial", 16))
        self.tags_entry.setStyleSheet(self.create_input_style())
        self.tags_entry.setGraphicsEffect(self.create_shadow_effect())
        left_layout.addWidget(self.tags_entry)

        # Create and add the notes label and entry
        notes_label = QLabel("Article Notes:")
        notes_label.setFont(QFont("Arial", 16))
        notes_label.setStyleSheet(f"color: {self.FONT_COLOR.name()}")
        left_layout.addWidget(notes_label)

        self.notes_entry = QTextEdit()
        self.notes_entry.setFont(QFont("Arial", 16))
        self.notes_entry.setStyleSheet(self.create_input_style())
        self.notes_entry.setGraphicsEffect(self.create_shadow_effect())
        left_layout.addWidget(self.notes_entry)

        # Create and add the generate button
        generate_button = QPushButton("Generate Article")
        generate_button.setFont(QFont("Arial", 16))
        generate_button.setStyleSheet(self.create_button_style())
        generate_button.clicked.connect(self.generate_article)
        left_layout.addWidget(generate_button)

        return left_layout

    def create_right_layout(self):
        """
        Create the right layout of the GUI.

        This layout includes a text browser to display the generated article.
        It is placed inside a scroll area to handle articles that exceed the
        display area. The layout also includes a label for the text browser.
        """

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(10, 10, 10, 10)

        # Create and add the generated article label
        self.generated_title_label = QLabel("Generated Article")
        self.generated_title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.generated_title_label.setStyleSheet(f"color: {self.FONT_COLOR.name()}")
        right_layout.addWidget(self.generated_title_label)

        # Create and add the text area for the generated article
        self.generated_text_area = QTextBrowser()
        self.generated_text_area.setReadOnly(True)
        self.generated_text_area.setFont(QFont("Arial", 16))
        self.generated_text_area.setStyleSheet(
            """
            QTextBrowser {
                border: none;
                border-radius: 5px;
                padding: 5px;
                background-color: %s;
                color: %s;
            }
            """
            % (self.INPUT_BOX_COLOR.name(), self.FONT_COLOR.name())
        )

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.generated_text_area)
        right_layout.addWidget(scroll_area)

        return right_layout

    def create_widget(self, layout):
        """
        Create a QWidget with the given layout.

        This utility method creates a new QWidget and sets its layout to the provided layout.
        It's used to encapsulate layouts in their own widgets, which is especially useful
        when adding them to a QSplitter. This allows for more modular and reusable layout
        creation.

        Parameters:
        layout (QLayout): The layout to set on the created QWidget.

        Returns:
        QWidget: The newly created widget with the given layout.
        """

        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def generate_article(self):
        """
        Trigger the article generation process.

        This method is connected to the 'Generate Article' button. It retrieves
        the text from input fields and starts a new thread to call the OpenAI API,
        preventing the GUI from freezing during the API request.
        """

        title = self.title_entry.text()
        tags = self.tags_entry.text()
        notes = self.notes_entry.toPlainText()
        self.ellipsis_timer.start(500)
        # Start a new thread for API call to avoid freezing the GUI
        threading.Thread(
            target=self.call_openai_api, args=(title, tags, notes), daemon=True
        ).start()

    def call_openai_api(self, title, tags, notes):
        """
        Call the OpenAI API to generate an article.

        This method runs in a separate thread to avoid blocking the GUI.
        It makes a request to the OpenAI API using the provided title, tags,
        and notes, then emits a signal when the article is generated.

        Parameters:
        title (str): The title of the article.
        tags (str): Tags associated with the article.
        notes (str): Additional notes or instructions for the article.
        """

        try:
            outline = generate_article_outline(title, notes, tags)
            generated_article = generate_full_article_from_outline(outline)
            self.articleGenerated.emit(generated_article)
        except Exception as e:
            print(e)  # Handle error

    def update_gui_with_generated_article(self, text):
        """
        Update the GUI with the generated article.

        This method is called when the article generation is complete. It stops
        the ellipsis timer, clears the text area, and starts the typing timer
        to display the article with a typing effect.

        Parameter:
        text (str): The generated article text to display.
        """

        self.ellipsis_timer.stop()  # Stop the ellipsis timer
        self.generated_text_area.clear()  # Clear the text area

        self.full_generated_text = text
        self.current_typing_position = 0
        self.typing_timer.start(30)  # Start the typing effect

    def type_next_character(self):
        """
        Simulate the typing effect by adding the next character to the text area.

        This method is connected to a timer that adds characters from the generated
        article to the text display, creating a typing animation effect.
        """

        if self.current_typing_position < len(self.full_generated_text):
            current_text = self.full_generated_text[self.current_typing_position]
            self.generated_text_area.insertPlainText(
                current_text
            )  # Insert next character
            self.current_typing_position += 1
        else:
            self.typing_timer.stop()

    def update_ellipsis(self):
        """
        Update the ellipsis animation during the loading phase.

        This method updates the text in the text area to include an ellipsis
        that 'animates' by changing its length, indicating a loading process.
        """

        self.ellipsis_count = (self.ellipsis_count + 1) % 4
        self.generated_text_area.setText(
            "Generating article" + "." * self.ellipsis_count
        )

    def finish_loading(self):
        """
        Testing method to simulate the completion of article loading.

        This method can be used to test the update functionality of the GUI
        without making an actual API request.
        """

        self.update_gui_with_generated_article("Sample generated article text.")


def main():
    """
    Main function to create and run the PyQt application.
    """
    app = QApplication(sys.argv)
    generator = ArticleGenerator()
    generator.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
