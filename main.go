package main

import (
	"embed"
	"golang.org/x/exp/maps"
	"gopkg.in/yaml.v3"
	"html/template"
	"io/fs"
	"log"
	"math/rand"
	"net/http"
	"path/filepath"
)

//go:embed hack/exams
var bank embed.FS

//go:embed static
var static embed.FS

type Question struct {
	Choices     map[string]string
	Explication string
	Solution    []string
	Text        string
}

type Bank struct {
	Questions map[string]Question
}

type Pair[T, U any] struct {
	First  T
	Second U
}

func loadQuestions() map[string]Question {
	directory := "hack/exams"
	files, err := bank.ReadDir(directory)
	if err != nil {
		log.Fatal("Error reading embedded directory:", err)
	}

	questions := make(map[string]Question)

	// Enumerate the files
	for _, file := range files {
		filename := file.Name()
		log.Println("Loading", filename)
		content, err := bank.ReadFile(filepath.Join(directory, filename))
		if err != nil {
			log.Fatal("Error reading file:", err)
		}

		var local Bank
		if err := yaml.Unmarshal(content, &local); err != nil {
			log.Fatal("Error parsing as YAML:", err)
		}

		maps.Copy(questions, local.Questions)
	}

	return questions
}

func getRandomQuestion(questions map[string]Question) (string, Question) {
	keys := maps.Keys(questions)

	key := keys[rand.Intn(len(keys))]
	value := questions[key]

	return key, value
}

func main() {
	questions := loadQuestions()

	log.Println("Loaded", len(questions), "questions")

	rootTemplate := template.New("index.gohtml").Funcs(template.FuncMap{
		"optionType": func(solution []string) string {
			if len(solution) == 1 {
				return "radio"
			}
			return "checkbox"
		},
		"shuffle": func(choices map[string]string) []Pair[string, string] {
			result := make([]Pair[string, string], len(choices))
			i := 0
			for k, v := range choices {
				result[i] = Pair[string, string]{
					First:  k,
					Second: v,
				}
				i++
			}

			// True or false questions should never be shuffled
			if len(result) == 2 {
				return result
			}

			rand.Shuffle(len(result), func(i, j int) {
				result[i], result[j] = result[j], result[i]
			})

			return result
		},
	})
	rootTemplate = template.Must(rootTemplate.ParseFS(static, "static/index.gohtml"))

	rootHandler := func(w http.ResponseWriter, r *http.Request) {
		_, question := getRandomQuestion(questions)
		err := rootTemplate.Execute(w, question)
		if err != nil {
			log.Fatal("Error executing template:", err)
		}
	}

	subFs, err := fs.Sub(static, "static")
	if err != nil {
		log.Fatal(err)
	}

	mux := http.NewServeMux()
	s := &http.Server{
		Addr:    ":8080",
		Handler: mux,
	}

	mux.HandleFunc("/{$}", rootHandler)
	mux.Handle("/css/", http.FileServer(http.FS(subFs)))

	log.Fatal(s.ListenAndServe())
}
