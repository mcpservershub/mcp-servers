package utils

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"

	log "github.com/sirupsen/logrus"
)

func PrettyPrint(data any) (string, error) {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to marshal data: %w", err)
	}
	return string(jsonData), nil
}

func MakeGetRequest(url string) ([]byte, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	tkn := getSonarToken()
	req.SetBasicAuth(tkn, "")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to perform request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	// read the body regardless, so we can include it in errors
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}
	// 200–299 is success
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("GET %q returned status %d: %s", url, resp.StatusCode, strings.TrimSpace(string(body)))
	}
	return body, nil
}

func getSonarToken() string {
	sonarToken := os.Getenv("SONAR_TOKEN")
	if sonarToken == "" {
		log.Fatal("SONAR_TOKEN environment variable is not set")
	}
	return sonarToken
}

// InterfacesToStringsOrEmpty will cast strings and skip everything else.
func InterfacesToStringsOrEmpty(vals []interface{}) []string {
	out := make([]string, 0, len(vals))
	for _, v := range vals {
		if s, ok := v.(string); ok {
			out = append(out, s)
		}
	}
	return out
}
