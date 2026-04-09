import customtkinter as ctk
import threading
import os
import winsound

class KUScoutApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("KU-Scout v1.0")
        self.geometry("500x450")

        self.label = ctk.CTkLabel(self, text="KU-Scout Exam Hunter", font=("Roboto", 24, "bold"))
        self.label.pack(pady=(20, 19))

        self.entry = ctk.CTkEntry(self, placeholder_text="Enter units (e.g Law of torts)", width=400)
        self.entry.pack(pady=10)
        self.year_entry = ctk.CTkEntry(self, placeholder_text="Enter Year (optional)", width=400)
        self.year_entry.pack(pady=10)

        self.download_button = ctk.CTkButton(self, text="Start download", command=self.start_hunt)
        self.download_button.pack(pady=20)

        self.textbox = ctk.CTkTextbox(self, width=450, height=150)
        self.textbox.pack(pady=10)

    def start_hunt(self):
        user_input = self.entry.get()
        units = [u.strip() for u in user_input.split(",")]
        year = self.year_entry.get().strip()
        self.download_button.configure(state="disabled", text="Hunting...")
        thread = threading.Thread(target=self.run_scraper, args=(units, year))
        thread.start()

    def update_log(self, message):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def run_scraper(self, units, year):
        import requests
        from bs4 import BeautifulSoup
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}
        
        save_path = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'KU_Semester_Exams')
        if not os.path.exists(save_path): os.makedirs(save_path)

        for unit in units:
            unit = unit.strip()
            if not unit: continue
            self.update_log(f"🔎 Searching for: {unit}...")

            query = f"{unit} {year}" if year else unit
            search_url = f"https://pastpapers.ku.ac.ke/discover?query={query.replace(' ', '+')}"

            try:
                response = requests.get(search_url, headers=headers, verify=False, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # UNIVERSAL SEARCH: Look for ANY link that looks like a paper handle
                papers = soup.find_all('a', href=lambda h: h and '/handle/' in h)
                self.update_log(f"📊 Debug: Found {len(papers)} potential matches.")

                if not papers:
                    self.update_log(f"   ❌ No exact papers found. Check spelling!")
                    continue

                # Get the link for the first result
                item_url = f"https://pastpapers.ku.ac.ke{papers[0].get('href')}"
                
                # Visit the specific paper page
                item_page = requests.get(item_url, headers=headers, verify=False)
                item_soup = BeautifulSoup(item_page.text, 'html.parser')

                # Find the actual PDF bitstream link
                download_link = None
                for link in item_soup.find_all('a', href=True):
                    if "/bitstream/" in link['href'] and ".pdf" in link['href'].lower():
                        download_link = link
                        break

                if download_link:
                    pdf_url = f"https://pastpapers.ku.ac.ke{download_link.get('href')}"
                    file_name = f"{unit.replace(' ', '_')}.pdf"
                    
                    self.update_log(f"   ⏳ Downloading PDF...")
                    pdf_data = requests.get(pdf_url, headers=headers, verify=False).content
                    with open(os.path.join(save_path, file_name), 'wb') as f:
                        f.write(pdf_data)
                    self.update_log(f"✅ Saved: {file_name}")
                    winsound.MessageBeep()
                else:
                    self.update_log(f"   ⏭️ Paper page found, but PDF is restricted or missing.")

            except Exception as e:
                self.update_log(f"   ⚠️ Error: {str(e)}")


        self.update_log("\n🏁 ALL DONE!")
        self.download_button.configure(state="normal", text="Start Download")

if __name__ == "__main__":
    app = KUScoutApp()
    app.mainloop()