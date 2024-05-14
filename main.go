package main

import (
	"context"
	"log"

	"github.com/gin-gonic/gin"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"

	"github.com/itsLeonB/genshin-furnishings/http"
	"github.com/itsLeonB/genshin-furnishings/repository"
)

func main() {
	// create a database connection
	client, err := mongo.NewClient(options.Client().ApplyURI("mongodb://127.0.0.1:27017"))
	if err != nil {
		log.Fatal(err)
	}
	if err := client.Connect(context.TODO()); err != nil {
		log.Fatal(err)
	}

	// create a repository
	repository := repository.NewRepository(client.Database("genshin-furnishings"))

	// create an http server
	server := http.NewServer(repository)

	// create a gin router
	router := gin.Default()
	{
		router.POST("/register", server.Register)
		router.GET("/users/:username", server.GetUser)
		router.POST("/users", server.CreateUser)
		router.PUT("/users/:username", server.UpdateUser)
		router.DELETE("/users/:username", server.DeleteUser)
	}

	// start the router
	router.Run(":9080")
}
