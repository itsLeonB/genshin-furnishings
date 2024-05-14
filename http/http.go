package http

import (
	"errors"
	"net/http"

	"github.com/gin-gonic/gin"

	"github.com/itsLeonB/genshin-furnishings/model"
	"github.com/itsLeonB/genshin-furnishings/repository"
)

type Server struct {
	repository repository.Repository
}

func NewServer(repository repository.Repository) *Server {
	return &Server{repository: repository}
}

func (s Server) Register(ctx *gin.Context) {
	var user model.User

	if err := ctx.ShouldBindJSON(&user); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "invalid request body"})
		return
	}

	if user.Username == "" || user.Password == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "username and password are required"})
		return
	}

	msg, err := s.repository.Register(ctx, user)

	if err != nil {
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	ctx.JSON(http.StatusOK, gin.H{"message": msg})
}

func (s Server) GetUser(ctx *gin.Context) {
	username := ctx.Param("username")
	if username == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "invalid argument username"})
		return
	}
	user, err := s.repository.GetUser(ctx, username)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, err.Error())
		return
	}
	ctx.JSON(http.StatusOK, gin.H{"user": user})
}

func (s Server) CreateUser(ctx *gin.Context) {
	var user model.User
	if err := ctx.ShouldBindJSON(&user); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "invalid request body"})
		return
	}
	user, err := s.repository.CreateUser(ctx, user)
	if err != nil {
		ctx.JSON(http.StatusInternalServerError, err.Error())
		return
	}
	ctx.JSON(http.StatusOK, gin.H{"user": user})
}

func (s Server) UpdateUser(ctx *gin.Context) {
	username := ctx.Param("username")
	if username == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "invalid argument username"})
		return
	}
	var user model.User
	if err := ctx.ShouldBindJSON(&user); err != nil {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "invalid request body"})
		return
	}
	user.Username = username
	user, err := s.repository.UpdateUser(ctx, user)
	if err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, err.Error())
		return
	}
	ctx.JSON(http.StatusOK, gin.H{"user": user})
}

func (s Server) DeleteUser(ctx *gin.Context) {
	username := ctx.Param("username")
	if username == "" {
		ctx.JSON(http.StatusBadRequest, gin.H{"error": "invalid argument username"})
		return
	}
	if err := s.repository.DeleteUser(ctx, username); err != nil {
		if errors.Is(err, repository.ErrUserNotFound) {
			ctx.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}
		ctx.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	ctx.JSON(http.StatusNoContent, gin.H{})
}
