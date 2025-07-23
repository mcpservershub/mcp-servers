package tools

type Component struct {
	Organization string `json:"organization"`
	Key          string `json:"key"`
	Enabled      bool   `json:"enabled"`
	Qualifier    string `json:"qualifier"`
	Name         string `json:"name"`
	LongName     string `json:"longName"`
	Path         string `json:"path"`
}

// const SONARQUBE_URL = "https://sonarcloud.io/"
const SONARQUBE_URL = "http://localhost:9000/"
