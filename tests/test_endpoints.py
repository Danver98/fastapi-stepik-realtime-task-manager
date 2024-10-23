import pytest
from httpx import AsyncClient
from app.api import schemas

REFRESH_TOKEN_HEADER = 'X-Refresh-Token'
FINGERPRINT_HEADER = 'X-Fingerprint'


class TestUserEndpoints:
    """Test user endpoints"""

    user_login = 'test-user'
    user_name = 'test-name'
    user_surname = 'test-surname'
    user_password = 'test-password'

    @pytest.mark.asyncio
    async def test_register_user(self, async_client: AsyncClient):
        """Test get user endpoint"""
        response = await async_client.post("/auth/register", data={
            "login": self.user_login,
            "name": self.user_name,
            "surname": self.user_surname,
            "password": self.user_password
            })
        assert response.status_code == 200
        result = response.json()
        assert result['login'] == self.user_login
        assert result['name'] == self.user_name
        assert result['surname'] == self.user_surname
        assert result['roles'] is None
        assert result['id'] is not None

    @pytest.mark.asyncio
    async def test_login_logout_user(self, async_client: AsyncClient):
        """Test login endpoint"""
        response = await async_client.post("/auth/login", data={
            "username": self.user_login,
            "password": self.user_password
            })
        assert response.status_code == 200
        response_data = response.json()
        assert 'access_token' in response_data
        assert 'token_type' in response_data
        assert 'refresh_token' in response_data
        assert 'fingerprint' in response_data
        assert 'logged_at' in response_data

        response = await async_client.post("/auth/logout", headers={
            FINGERPRINT_HEADER: response_data['fingerprint'],
            'Authorization': 'Bearer ' + response_data['access_token']
        })

        assert response.status_code == 200
        assert response.json() == {
            'user': self.user_login,
            'status': 'logged out'
        }


class TestTaskEndpoints:
    """Test task endpoints"""

    user_login = 'test-user2'
    user_name = 'test-name2'
    user_surname = 'test-surname2'
    user_password = 'test-password2'
    task_names = [
        f'test-name-{i}' for i in range(3)
    ]
    task_descriptions = [
        f'test-description-{i}' for i in range(3)
    ]

    @pytest.mark.asyncio
    async def test_task_operations_without_auth(self, async_client: AsyncClient):
        """
            Test task operations without authentication.
            1) Try to create task without authentication
            2) Try to get list of tasks without authentication
        """
        # 1. Check task creation
        task = schemas.Task(
            name=self.task_names[0],
            description=self.task_descriptions[0]
        )
        response = await async_client.post("/tasks/create", json=task.model_dump())
        assert response.status_code == 401

        # 2. Check task list
        response = await async_client.get("/tasks/read-all/0")
        assert response.status_code == 401


    @pytest.mark.asyncio
    async def test_task_operations_auth(self, async_client: AsyncClient):
        """Test task operations with authentication"""
        # 0. Register user
        response = await async_client.post("/auth/register", data={
            "login": self.user_login,
            "name": self.user_name,
            "surname": self.user_surname,
            "password": self.user_password
            })
        assert response.status_code == 200
        user_id = response.json()['id']
        # 1 login
        response = await async_client.post("/auth/login", data={
            "username": self.user_login,
            "password": self.user_password
            })
        assert response.status_code == 200
        login_response_data = response.json()
        headers = {
            FINGERPRINT_HEADER: login_response_data['fingerprint'],
            'Authorization': 'Bearer ' + login_response_data['access_token']   
        }
        # 2. Create task
        task = schemas.Task(
            name=self.task_names[0],
            description=self.task_descriptions[0],
            user_id=user_id
        )
        response = await async_client.post("/tasks/create", json=task.model_dump(), headers=headers)
        assert response.status_code == 200
        created_task = response.json()
        # 3. Update task
        task = schemas.Task(**created_task)
        task.description = task.description + ' updated'
        task.completed = True
        response = await async_client.put("/tasks/update", json=task.model_dump(exclude={'created_at'}),
                                          headers=headers)
        assert response.status_code == 200
        # 4. Read task to check updates
        response = await async_client.get(f"/tasks/read/{task.id}", headers=headers)
        assert response.status_code == 200
        result = response.json()
        assert task == schemas.Task(**result)
        # 5. Create second task
        task2 = schemas.Task(
            name=self.task_names[2],
            description=self.task_descriptions[2],
            user_id=user_id
        )
        response = await async_client.post("/tasks/create", json=task2.model_dump(), headers=headers)
        assert response.status_code == 200
        task2 = schemas.Task(**response.json())
        # 6. Get all tasks
        response = await async_client.get(f"/tasks/read-all/{user_id}", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert task.id == tasks[0]['id']
        assert task2.id == tasks[1]['id']
        # 7. Delete first task
        response = await async_client.delete(f"/tasks/delete/{task.id}", headers=headers)
        assert response.status_code == 200
        # 8. Get all tasks
        response = await async_client.get(f"/tasks/read-all/{user_id}", headers=headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert task2.id == tasks[0]['id']
        # 9 Get second task with mangled token
        response = await async_client.get(f"/tasks/read/{task2.id}", headers={
            FINGERPRINT_HEADER: login_response_data['fingerprint'],
            'Authorization': 'Bearer ' + login_response_data['access_token'] + 'mangled'
        })
        assert response.status_code == 401

        # 10 Get second task without token
        response = await async_client.get(f"/tasks/read/{task2.id}", headers={
            FINGERPRINT_HEADER: login_response_data['fingerprint']
        })
        assert response.status_code == 401
